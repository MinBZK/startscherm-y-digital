import dataclasses
import os
from pathlib import Path
from config import Config
from nextcloud import NextCloudConnector
from state_manager import StateManager
import hashlib
from content import ContentExtractor
from elastic import ESClient
from utils import logger, hash, SUPPORTED_EXTENSIONS
from typing import Iterator


@dataclasses.dataclass
class Ingestor:
    config: Config
    nc: NextCloudConnector | None = None
    es: ESClient | None = None
    extractor: ContentExtractor | None = None
    state_manager: StateManager | None = None

    def __post_init__(self):
        if self.nc is None:
            self.nc = NextCloudConnector()
        if self.es is None:
            self.es = ESClient(self.config.dry_run)
        if self.extractor is None:
            self.extractor = ContentExtractor()
        if self.state_manager is None:
            self.state_manager = StateManager(self.config)

    # ------------- Public API -------------
    async def run_full_ingest(self, dry_run: bool = False) -> None:
        logger.info("Starting full ingest")
        logger.info(f"{dry_run=}")
        assert self.nc and self.es and self.extractor

        if dry_run:
            logger.info("Dry run mode enabled")
            self.es.dry_run = True

        logger.info("Creating indices if they do not exist")
        self.es.create_indices()

        logger.info("Listing users")
        users = await self.nc.list_users()
        logger.info(f"Found {len(users)} users")

        dossiers_to_index: list[dict] = []
        docs_to_index: list[dict] = []

        for user in users:
            logger.debug("Processing user %s", user)
            user_root = Path("/") / user
            parent = user_root / self.config.dossier_parent_path
            parent_str = str(parent)
            logger.debug(f"User {user}: checking parent path: {parent_str}")
            if not self.nc.is_dir(parent_str):
                logger.warning(
                    "User %s: parent path not found: %s",
                    user,
                    parent_str,
                )
                continue
            else:
                logger.debug(f"User {user}: found parent path: {parent_str}")
            dossier_names = [
                d for d in self.nc.listdir(parent_str)
                if self.nc.is_dir(str(parent / d))
            ]
            logger.debug(f"User {user}: found {len(dossier_names)} dossiers: {dossier_names}")

            for dossier_name in dossier_names:
                dossier_path = parent / dossier_name
                dossier_path_str = str(dossier_path)
                dossier_id = self._dossier_id(user, dossier_name)
                # Dossier metadata
                file_count, total_size, first_created = self._collect_tree_stats(
                    dossier_path_str
                )
                sharees = await self.nc.get_sharees(dossier_path)
                sharees.add(user)  # owner always has access
                
                file_id = await self._get_file_id(dossier_path_str, dossier_name)
                dossier_doc = {
                    "dossier_id": dossier_id,
                    "dossier_name": dossier_name,
                    "webURL": dossier_path_str,
                    "file_id": file_id,
                    "owner_userid": user,
                    "members": list(sharees),
                    "created_datetime": first_created,
                    "lastmodified_datetime": None,  # TODO: most recent file mod?
                    "type": "dossier",
                    "unopened": True,  # TODO:
                    "description": "",  # TODO:
                }
                
                logger.info(f"Creating dossier document for {dossier_name}: file_id={file_id}, webURL={dossier_path_str}")
                dossiers_to_index.append(dossier_doc)

                # Walk files
                for file_path in self._iter_files(dossier_path_str):
                    try:
                        doc = await self._build_document(
                            user=user,
                            dossier=dossier_doc,
                            path=file_path,
                        )
                        logger.debug(f"Built document: {doc}")
                        docs_to_index.append(doc)
                    except Exception as e:
                        logger.exception(
                            "Failed to process file %s: %s",
                            file_path,
                            e,
                        )
                        raise e

        logger.info(f"Final summary: Found {len(dossiers_to_index)} dossiers to index")
        logger.debug(f"Dossiers to index: {dossiers_to_index}")
        if dossiers_to_index:
            logger.info("Starting indexing of %d dossiers", len(dossiers_to_index))
            try:
                self.es.do_index_dossiers(dossiers_to_index)
                logger.info("Successfully indexed %d dossiers", len(dossiers_to_index))
            except Exception as e:
                logger.error(f"Failed to index dossiers: {e}")
                raise
        else:
            logger.warning("No dossiers found to index!")
        logger.debug(f"Documents to index: {docs_to_index}")
        if docs_to_index:
            logger.info("Indexing %d documents", len(docs_to_index))
            self.es.do_index_documents(docs_to_index)
            logger.info("Indexed %d documents", len(docs_to_index))

        # Update activity state to latest activity ID after full ingestion
        # This ensures incremental ingestion starts from the right point
        try:
            logger.info("Updating activity state after full ingestion")
            self.state_manager.initialize_schema()
            
            # Get the latest activity ID from NextCloud efficiently
            latest_activity_id = await self.nc.get_latest_activity_id()
            
            if latest_activity_id > 0:
                self.state_manager.update_activity_state(latest_activity_id)
                logger.info(f"Updated activity state to latest ID: {latest_activity_id}")
            else:
                logger.info("No activities found, keeping activity state at 0")
                
        except Exception as e:
            logger.error(f"Failed to update activity state after full ingestion: {e}")
            # Don't fail the entire ingestion for this
        finally:
            if self.state_manager:
                self.state_manager.close()

        logger.info("Ingest complete")

    async def run_incremental_ingest(self, dry_run: bool = False, fallback_to_full: bool = True) -> None:
        """Run incremental ingest based on NextCloud activity API."""
        logger.info("Starting incremental ingest")
        assert self.nc and self.es and self.extractor and self.state_manager

        if dry_run:
            logger.info("Dry run mode enabled")
            self.es.dry_run = True

        try:
            # Initialize state tracking
            self.state_manager.initialize_schema()
            
            # Get last processed activity ID
            last_activity_id, last_check_time = self.state_manager.get_last_activity_state()
            logger.info(f"Last processed activity ID: {last_activity_id}, last check: {last_check_time}")
            
            # Get activities since last check
            try:
                activity_data = await self.nc.get_activities_since(last_activity_id)
                activities = activity_data.get("ocs", {}).get("data", [])
            except Exception as e:
                logger.error(f"Failed to get activities: {e}")
                if fallback_to_full:
                    logger.info("Falling back to full ingest due to activity API failure")
                    return await self.run_full_ingest(dry_run=dry_run)
                else:
                    raise

            if not activities:
                logger.info("No new activities to process")
                return

            # Filter out activities with IDs <= last_activity_id to ensure we only process newer ones
            newer_activities = []
            filtered_count = 0
            for activity in activities:
                activity_id = activity.get("activity_id", 0)
                if activity_id > last_activity_id:
                    newer_activities.append(activity)
                else:
                    filtered_count += 1
                    logger.debug(f"Filtered out activity ID {activity_id} (<= {last_activity_id})")
            
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} activities with IDs <= {last_activity_id}")
            
            if not newer_activities:
                logger.info("No newer activities to process after filtering")
                # Still update the activity ID to the latest one we saw
                if activities:
                    latest_activity_id = max(a.get("activity_id", 0) for a in activities)
                    self.state_manager.update_activity_state(latest_activity_id)
                return

            # Process new dossiers first (from all activities, not just file activities)
            await self._process_new_dossiers(newer_activities)

            # Filter to file-related activities
            file_activities = await self.nc.filter_file_activities(newer_activities)
            if not file_activities:
                logger.info("No file-related activities to process")
                # Still update the activity ID to the latest one we saw
                if newer_activities:
                    latest_activity_id = max(a.get("activity_id", 0) for a in newer_activities)
                    self.state_manager.update_activity_state(latest_activity_id)
                return

            # Extract file paths by action type
            file_paths = await self.nc.extract_file_paths_from_activities(file_activities)
            created_files = file_paths["created"]
            updated_files = file_paths["updated"] 
            deleted_files = file_paths["deleted"]

            # Process deletions first
            if deleted_files:
                logger.info(f"Processing {len(deleted_files)} deleted files")
                await self._process_deleted_files(deleted_files)

            # Process created and updated files
            files_to_process = created_files | updated_files
            if files_to_process:
                logger.info(f"Processing {len(files_to_process)} created/updated files")
                await self._process_changed_files(files_to_process)

            # Update the last processed activity ID (using all newer activities, not just file activities)
            latest_activity_id = max(a.get("activity_id", 0) for a in newer_activities)
            self.state_manager.update_activity_state(latest_activity_id)
            
            logger.info(f"Incremental ingest complete. Processed {len(file_activities)} activities (latest ID: {latest_activity_id})")

        except Exception as e:
            logger.error(f"Incremental ingest failed: {e}")
            if fallback_to_full:
                logger.info("Falling back to full ingest due to error")
                return await self.run_full_ingest(dry_run=dry_run)
            else:
                raise
        finally:
            if self.state_manager:
                self.state_manager.close()


    async def _get_file_id(self, dossier_path: str, dossier_name: str) -> str | None:
        assert self.nc

        # Get dossier folder metadata including file ID
        file_id = None
        
        # Method 1: Try simple WebDAV with multiple ID fields
        try:
            file_id = await self.nc.get_folder_file_id_simple(dossier_path)
            if file_id:
                logger.info(f"Retrieved file_id {file_id} for dossier {dossier_name} using simple method")
                return file_id
        except Exception as e:
            logger.warning(f"Simple method failed for dossier {dossier_name}: {e}")
        
        # Method 2: Try original WebDAV metadata method
        if not file_id:
            try:
                dossier_metadata = self.nc.get_metadata(dossier_path)
                file_id = dossier_metadata.get("fileid")
                if file_id:
                    logger.info(f"Retrieved file_id {file_id} for dossier {dossier_name} using metadata method")
                    return file_id
            except Exception as e:
                logger.warning(f"Metadata method failed for dossier {dossier_name}: {e}")

        # Method 3: Try activity API method as last resort
        if not file_id:
            try:
                file_id = await self.nc.get_folder_file_id_from_activity(dossier_path)
                if file_id:
                    logger.info(f"Retrieved file_id {file_id} for dossier {dossier_name} from activity API")
                    return file_id
            except Exception as e:
                logger.warning(f"Activity API method failed for dossier {dossier_name}: {e}")
        
        if not file_id:
            logger.error(f"All methods failed to get file_id for dossier {dossier_name}")
        else:
            logger.info(f"Final file_id for dossier {dossier_name}: {file_id}")
        return


    async def _process_new_dossiers(self, activities: list[dict]):
        """Process activities to detect and index new dossier creation."""
        dossiers_to_index = []
        
        for activity in activities:
            activity_type = activity.get("type", "")
            
            # Look for file_created activities which can contain folder creation
            if activity_type != "file_created":
                continue
            
            # Collect all potential folder paths from the activity
            potential_folders = []
            
            # Check main object_name
            object_name = activity.get("object_name", "")
            if object_name:
                potential_folders.append(object_name)
            
            # Check all objects in the activity
            objects = activity.get("objects", {})
            for obj_id, obj_path in objects.items():
                potential_folders.append(obj_path)
            
            # Also check subject_rich for additional folder information
            subject_rich = activity.get("subject_rich", [])
            if len(subject_rich) >= 2 and isinstance(subject_rich[1], dict):
                for key, file_info in subject_rich[1].items():
                    if isinstance(file_info, dict) and file_info.get("type") == "file":
                        path = file_info.get("path", "")
                        if path:
                            # Add the path and also check if it's a folder path
                            potential_folders.append("/" + path)
                            # Extract potential parent folder from file path
                            folder_path = str(Path("/" + path).parent)
                            if folder_path != "/" and folder_path not in potential_folders:
                                potential_folders.append(folder_path)
            
            # Process each potential folder to see if it's a new dossier
            processed_dossiers = set()  # Avoid duplicates
            for folder_path in potential_folders:
                if not self._is_dossier_folder_path(folder_path):
                    continue
                    
                # Extract user and dossier name from the path
                user = self.nc.nc_user  # Use the authenticated user
                dossier_name = self._extract_dossier_name_from_path(folder_path)
                if not dossier_name:
                    logger.debug(f"Could not extract dossier name from path: {folder_path}")
                    continue
                    
                dossier_id = self._dossier_id(user, dossier_name)
                
                # Skip if we've already processed this dossier in this activity
                if dossier_id in processed_dossiers:
                    continue
                processed_dossiers.add(dossier_id)
                
                # Check if dossier already exists in ES
                if self.es.dossier_exists(dossier_id):
                    logger.debug(f"Dossier {dossier_id} already exists, skipping")
                    continue
                
                # Ensure path includes user prefix for WebDAV operations
                if not folder_path.startswith(f"/{user}/"):
                    full_dossier_path = f"/{user}{folder_path}" if folder_path.startswith("/") else f"/{user}/{folder_path}"
                else:
                    full_dossier_path = folder_path if folder_path.startswith("/") else f"/{folder_path}"
                
                # Verify the folder still exists
                if not self.nc.is_dir(full_dossier_path):
                    logger.debug(f"Dossier folder no longer exists: {full_dossier_path}")
                    continue
                
                try:
                    logger.info(f"Processing new dossier: {dossier_name} at {full_dossier_path}")
                    
                    # Collect statistics
                    file_count, total_size, first_created = self._collect_tree_stats(full_dossier_path)
                    
                    # Get sharees
                    sharees = await self.nc.get_sharees(full_dossier_path)
                    sharees.add(user)  # owner always has access

                    file_id = await self._get_file_id(folder_path.lstrip("/"), dossier_name)

                    dossier_doc = {
                        "dossier_id": dossier_id,
                        "file_id": file_id,
                        "dossier_name": dossier_name,
                        "webURL": folder_path,  # Use original path without user prefix
                        "owner_userid": user,
                        "members": list(sharees),
                        "created_datetime": first_created,
                        "lastmodified_datetime": None,  # TODO: most recent file mod?
                        "type": "dossier",
                        "unopened": True,
                        "description": "",
                        "file_count": file_count,
                        "total_size": total_size,
                    }
                    dossiers_to_index.append(dossier_doc)
                    logger.info(f"Detected new dossier: {dossier_name} (ID: {dossier_id})")
                    
                except Exception as e:
                    logger.error(f"Failed to build dossier metadata for {folder_path}: {e}")
                
        # Index all new dossiers
        if dossiers_to_index:
            logger.info(f"Indexing {len(dossiers_to_index)} new dossiers")
            for dossier in dossiers_to_index:
                self.es.index_new_dossier(dossier)


    def _is_dossier_folder_path(self, folder_path: str) -> bool:
        """Check if the folder path represents a dossier (i.e., is directly under the dossier parent path)."""
        path = Path(folder_path)
        parts = path.parts
        
        # Must contain the dossier parent path
        dossier_parent = self.config.dossier_parent_path
        if dossier_parent not in parts:
            return False
            
        try:
            parent_index = parts.index(dossier_parent)
            # The folder should be exactly one level below the dossier parent
            # e.g., if path is "Documenten/MyDossier", and dossier_parent is "Documenten"
            # then this should be a dossier folder
            return parent_index + 1 < len(parts) and parent_index + 2 == len(parts)
        except ValueError:
            return False

    async def _process_deleted_files(self, deleted_files: set[str]):
        """Process file deletions by removing from ES and updating dossier stats."""
        for file_path in deleted_files:
            try:
                # Get document info before deletion for dossier stat updates
                doc_info = self.es.get_document_info(file_path)
                
                # Delete the document from ES
                self.es.delete_documents_by_path({file_path})
                
                # Update dossier stats if we had document info
                if doc_info:
                    dossier_id = doc_info.get("dossier_id")
                    file_size = int(doc_info.get("size", 0))
                    if dossier_id:
                        self.es.update_dossier_stats(dossier_id, file_count_delta=-1, size_delta=-file_size)
                        logger.debug(f"Updated dossier {dossier_id} stats after deleting {file_path}")
                        
            except Exception as e:
                logger.error(f"Failed to process deletion of {file_path}: {e}")

    async def _process_changed_files(self, changed_files: set[str]):
        """Process created/updated files by re-indexing them."""
        docs_to_index = []
        
        for file_path in changed_files:
            try:
                # Check if file still exists and is within a dossier
                if not self._is_file_in_dossier_structure(file_path):
                    logger.debug(f"Skipping file not in dossier structure: {file_path}")
                    continue
                
                # Ensure path includes user prefix for WebDAV operations
                if not file_path.startswith(f"{self.nc.nc_user}/"):
                    full_file_path = f"/{self.nc.nc_user}/{file_path}"
                else:
                    full_file_path = f"/{file_path}" if not file_path.startswith("/") else file_path
                    
                # Check parent directory and file existence
                parent_path = str(Path(full_file_path).parent)
                if not self.nc.is_dir(parent_path) or not self._file_exists(file_path):
                    logger.debug(f"File no longer exists, skipping: {file_path}")
                    continue
                
                # Determine user and dossier from path (use original path without user prefix for processing)
                path_parts = Path(file_path).parts
                if len(path_parts) < 2:  # Must have at least dossier_parent/dossier/file
                    logger.debug(f"Invalid path structure, skipping: {file_path}")
                    continue
                    
                user = self.nc.nc_user  # Use the authenticated user
                dossier_name = self._extract_dossier_name_from_path(file_path)
                if not dossier_name:
                    logger.debug(f"Could not extract dossier name from path: {file_path}")
                    continue
                    
                dossier_id = self._dossier_id(user, dossier_name)
                
                # Check if document already exists (for stat updates)
                was_existing = self.es.document_exists(file_path)
                existing_doc_info = None
                if was_existing:
                    existing_doc_info = self.es.get_document_info(file_path)
                
                # Build the document (use full path for WebDAV operations)
                doc = await self._build_document_incremental(user, dossier_id, full_file_path)
                docs_to_index.append(doc)
                
                # Update dossier stats
                new_file_size = int(doc.get("size", 0))
                if was_existing and existing_doc_info:
                    # File updated - only update size delta
                    old_file_size = int(existing_doc_info.get("size", 0))
                    size_delta = new_file_size - old_file_size
                    if size_delta != 0:
                        self.es.update_dossier_stats(dossier_id, file_count_delta=0, size_delta=size_delta)
                else:
                    # New file - increment count and add size
                    self.es.update_dossier_stats(dossier_id, file_count_delta=1, size_delta=new_file_size)
                    
            except Exception as e:
                logger.error(f"Failed to process changed file {file_path}: {e}")
                
        # Index all processed documents
        if docs_to_index:
            self.es.do_index_documents(docs_to_index)
            logger.info(f"Indexed {len(docs_to_index)} changed documents")

    def _is_file_in_dossier_structure(self, file_path: str) -> bool:
        """Check if file path is within the expected dossier structure."""
        path = Path(file_path)
        if len(path.parts) < 3:
            return False
            
        # Check if the path contains the dossier parent path
        dossier_parent = self.config.dossier_parent_path
        return dossier_parent in path.parts

    def _extract_dossier_name_from_path(self, file_path: str) -> str | None:
        """Extract dossier name from file path."""
        path = Path(file_path)
        parts = path.parts
        
        # Find the dossier parent path
        dossier_parent = self.config.dossier_parent_path
        try:
            parent_index = parts.index(dossier_parent)
            if parent_index + 1 < len(parts):
                return parts[parent_index + 1]
        except ValueError:
            pass
            
        return None

    def _file_exists(self, file_path: str) -> bool:
        """Check if file exists in NextCloud via WebDAV."""
        try:
            # Ensure path includes user prefix for WebDAV operations
            if not file_path.startswith(f"{self.nc.nc_user}/"):
                full_path = f"/{self.nc.nc_user}/{file_path}"
            else:
                full_path = f"/{file_path}" if not file_path.startswith("/") else file_path
            self.nc.get_metadata(full_path)
            return True
        except Exception:
            return False

    # ------------- Internals -------------
    def _dossier_id(self, user: str, dossier_name: str) -> str:
        raw = f"{user}:{dossier_name}".encode("utf-8")
        return hashlib.sha1(raw).hexdigest()  # stable, short id

    def _iter_files(self, root: str) -> Iterator[str]:
        queue = [Path(root)]
        while queue:
            current = queue.pop(0)
            current_str = str(current)
            entries = self.nc.listdir(current_str)
            for name in entries:
                path = current / name
                path_str = str(path)
                if self.nc.is_dir(path_str):
                    queue.append(path)
                else:
                    logger.debug(f"Found file: {path_str}, yielding")
                    yield path_str

    def _collect_tree_stats(self, root: str) -> tuple[int, int, str | None]:
        count = 0
        total = 0
        created_candidates: list[str] = []
        for path in self._iter_files(root):
            meta = self.nc.get_metadata(path)
            logger.debug(f"File {path} metadata: {meta}")
            count += 1
            try:
                total += int(meta.get("size", 0))
            except Exception:
                pass
            created = meta.get("created") or meta.get("modified") or ""
            if created:
                created_candidates.append(created)
        created_str = min(created_candidates) if created_candidates else None
        return count, total, created_str

    def _normalize_date(self, date_str: str) -> str | None:
        """Normalize date string to ISO 8601 format or return None."""
        if not date_str or date_str == "":
            return None
        
        # Try parsing common formats
        import datetime
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%a, %d %b %Y %H:%M:%S %Z"):
            try:
                dt = datetime.datetime.strptime(date_str, fmt)
                return dt.isoformat() + "Z"
            except ValueError:
                continue
        
        logger.warning(f"Unrecognized date format: {date_str}")
        return None

    async def _build_document(self, user: str, dossier: dict, path: str) -> dict:
        # Fetch file content (for hashing and extraction)
        content = self.nc.read_file(path)

        # Basic metadata
        stat = self.nc.get_metadata(path)
        nextcloud_id = stat.get("fileid", None)
        size = int(stat.get("size", 0))
        modified = stat.get("modified", None)
        created = stat.get("created", None) or modified  # Use None instead of empty string
        # Normalize empty strings to None for date fields
        if created == "":
            created = None
        if modified == "":
            modified = None
        
        # Normalize dates to ISO 8601 format
        created = self._normalize_date(created)
        modified = self._normalize_date(modified)
        
        filetype = stat.get("type", None)
        sharees = await self.nc.get_sharees(path)
        sharees.add(user)

        last_modified_user = await self.nc.get_last_modified_user_async(nextcloud_id)

        # MIME & extension
        ext = os.path.splitext(path)[1].lower()

        # Extraction
        full_text = ""
        if ext in SUPPORTED_EXTENSIONS:
            full_text = self.extractor.extract(path, content)
        paragraphs = self.parse(full_text)

        # Build schema-compliant doc
        title = os.path.basename(path)
        doc = {
            "title": title,
            "raw_title": title,
            "retention_period": None,
            "nextcloud_id": nextcloud_id,
            "url": path,
            "werkproces": None,
            "author": user,
            "author_id": user,
            "author_modified": None,
            "bewaartermijn": None,
            "created_date": created,
            "datetime_published": None,
            "description": None,
            "accessible_to_users": list(sharees),
            "dossier_id": dossier["dossier_id"],
            "dossier_name": dossier["dossier_name"],
            "filepath": path,
            "drive_id": None,
            "lastmodifiedtime": modified,
            "filetype": filetype,
            "full_text": full_text,
            "keywords": [],
            "last_annotated": None,
            "lastmodified_user_id": last_modified_user or user,
            "needs_download": "no",
            "needs_annotation": "no",
            "number_pages": None,
            "paragraphs": paragraphs,
            "size": size,
            "summary": None,
            
        }
        return doc

    async def _build_document_incremental(self, user: str, dossier_id: str, full_path: str) -> dict:
        """Build document for incremental processing when we only have dossier_id."""
        # Extract the original path without user prefix for document storage
        if full_path.startswith(f"/{user}/"):
            original_path = full_path[len(f"/{user}/"):]
        else:
            original_path = full_path.lstrip("/")  # Remove leading slash if no user prefix
            
        # Fetch file content (for hashing and extraction) using full path
        content = self.nc.read_file(full_path)

        # Basic metadata using full path
        stat = self.nc.get_metadata(full_path)
        nextcloud_id = stat.get("fileid", None)
        size = int(stat.get("size", 0))
        modified = self._normalize_date(stat.get("modified", None))
        created = self._normalize_date(stat.get("created", modified))
        filetype = stat.get("type", None)
        sharees = await self.nc.get_sharees(full_path)
        sharees.add(user)

        # MIME & extension using original path
        ext = os.path.splitext(original_path)[1].lower()

        # Extraction using full path for file access, but original path for reference
        full_text = ""
        if ext in SUPPORTED_EXTENSIONS:
            full_text = self.extractor.extract(full_path, content)
        paragraphs = self.parse(full_text)

        # Extract dossier name from original path (reverse of _dossier_id)
        dossier_name = self._extract_dossier_name_from_path(original_path) or "unknown"

        # Build schema-compliant doc using original path
        title = os.path.basename(original_path)
        doc = {
            "title": title,
            "raw_title": title,
            "retention_period": None,
            "nextcloud_id": nextcloud_id,
            "url": original_path,  # Use original path for consistency
            "werkproces": None,
            "author": user,
            "author_id": user,
            "author_modified": None,
            "bewaartermijn": None,
            "created_date": created,
            "datetime_published": None,
            "description": None,
            "accessible_to_users": list(sharees),
            "dossier_id": dossier_id,
            "dossier_name": dossier_name,
            "filepath": original_path,
            "drive_id": None,
            "lastmodifiedtime": modified,
            "filetype": filetype,
            "full_text": full_text,
            "keywords": [],
            "last_annotated": None,
            "lastmodified_user_id": user,
            "needs_download": "no",
            "needs_annotation": "no",
            "number_pages": None,
            "paragraphs": paragraphs,
            "size": size,
            "summary": None,
            
        }
        return doc
    
    def parse(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return [
            {"id": i, "text": p}
            for i, p in enumerate(paragraphs)
        ]
    

