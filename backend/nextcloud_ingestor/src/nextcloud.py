import os
from pathlib import Path
import httpx
import webdav3
from webdav3.client import Client as WebDAVClient
from utils import logger
import xml.etree.ElementTree as ET

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except ImportError:
    pass  # dotenv not available, use system env vars

# ENV
NC_URL = os.getenv("NC_URL") or os.getenv("NEXTCLOUD_URL", "http://localhost:8080")
NC_USER = os.getenv("NC_USER") or os.getenv("NEXTCLOUD_ADMIN_USERNAME", "admin")
NC_PASSWORD = os.getenv("NC_PASSWORD") or os.getenv("NEXTCLOUD_ADMIN_PASSWORD", "adminpassword")


class NextCloudConnector:
    def __init__(self):
        # Log the configuration being used
        logger.info(f"NextCloudConnector initialized with NC_URL={NC_URL}, NC_USER={NC_USER}")
        
        # Store user for path operations
        self.nc_user = NC_USER
        
        # webdavclient
        self.base_url = NC_URL.rstrip("/")
        self.files_root = self.base_url + "/remote.php/dav/files/"
        options = {
            "webdav_hostname": str(self.files_root),
            "webdav_login": NC_USER,
            "webdav_password": NC_PASSWORD,
            "disable_check": True,  # avoid HEAD check on init
        }
        self.webdavclient = WebDAVClient(options)

        self.nc_auth = (NC_USER, NC_PASSWORD)

        # for direct API calls
        self.api_headers = {
            "OCS-APIRequest": "true",   # required for OCS API calls
            "Accept": "application/json"  # request JSON instead of XML
        }

        # xml header
        self.xml_header = {
            "Content-Type": "application/xml",
            "Depth": "0"
        }

        self.usergroups: dict[str, list[str]] | None = None

    def listdir(self, path: str) -> list[str]:
        raw = self.webdavclient.list(path) or []
        items = []
        for p in raw[1:]:
            if p.endswith("/"):
                p = p[:-1]
            name = p.rsplit("/", 1)[-1] if "/" in p else p
            if name in (".", ".."):
                continue
            if name == "":
                continue
            items.append(name)
        return items

    def is_dir(self, path: str) -> bool:
        try:
            return self.webdavclient.resource(path).is_dir()
        except webdav3.exceptions.RemoteResourceNotFound:
            return False

    def read_file(self, path: str) -> bytes:
        url = self.webdavclient.get_url(path)
        resp = self.webdavclient.session.get(
            url,
            auth=self.nc_auth,
            stream=True
        )
        resp.raise_for_status()
        return resp.content

    def get_metadata(self, path: str) -> dict[str, str]:
        info = self.webdavclient.info(path)
        
        size = int(info.get("size", 0)) if isinstance(info.get("size"), (str, int)) else 0
        modified = info.get("modified") or info.get("Last-Modified") or ""
        created = info.get("created") or info.get("CreationDate") or ""
        return {
            "size": str(size),
            "modified": modified,
            "created": created,
            "type": info.get("content_type", ""),
            "fileid": self._get_file_id(path),
            "etag": info.get("etag").strip('"') or None,
        }
    
    def _get_file_id(self, path: str) -> str | None:
        try:
            xml_body = """<?xml version="1.0"?>
            <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
            <d:prop>
                <oc:fileid/>
                <d:resourcetype/>
            </d:prop>
            </d:propfind>
            """

            url = self.webdavclient.get_url(path)
            resp = self.webdavclient.session.request(
                "PROPFIND",
                url,
                auth=self.nc_auth,
                headers=self.xml_header,
                data=xml_body
            )
            resp.raise_for_status()

            ns = {"d": "DAV:", "oc": "http://owncloud.org/ns"}
            root = ET.fromstring(resp.content)
            
            # Debug: log the full response
            logger.debug(f"WebDAV response for {path}: {resp.content.decode('utf-8')}")
            
            fileid_elem = root.find(".//oc:fileid", ns)
            if fileid_elem is not None and fileid_elem.text:
                logger.debug(f"Found fileid {fileid_elem.text} for {path}")
                return fileid_elem.text
            else:
                logger.debug(f"No fileid found in WebDAV response for {path}")
            return None
        
        except Exception as e:
            logger.error(f"Error fetching file ID for {path}: {e}")
            return None

    async def list_users(self) -> list[str]:
        logger.info("Listing users from NextCloud")
        try:
            # Add timeout to prevent hanging
            timeout = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(auth=self.nc_auth, timeout=timeout) as client:
                logger.debug(f"Making request to: {NC_URL}/ocs/v1.php/cloud/users")
                resp = await client.get(
                    NC_URL + "/ocs/v1.php/cloud/users", 
                    headers=self.api_headers
                )
                logger.debug(f"Response status code: {resp.status_code}, Response text: {resp.text}")

                if resp.status_code == 200:
                    data = resp.json()
                    users = data["ocs"]["data"]["users"]
                    logger.info(f"Successfully retrieved {len(users)} users from NextCloud")
                    logger.info(f"Users: {users}")
                    return users
                else:
                    logger.error(f"Error listing users from NextCloud: {resp.status_code} {resp.text}")
                    return []
        except httpx.TimeoutException as e:
            logger.error(f"Timeout occurred while listing users from NextCloud: {e}")
            return []
        except Exception as e:
            logger.error(f"Exception occurred while listing users from NextCloud: {e}")
            return []
            
    async def list_groups(self) -> list[str]:
        logger.info("Listing groups from NextCloud")
        try:
            async with httpx.AsyncClient(auth=self.nc_auth) as client:
                resp = await client.get(
                    NC_URL + "/ocs/v1.php/cloud/groups",
                    headers=self.api_headers
                )

                if resp.status_code == 200:
                    data = resp.json()
                    groups = data["ocs"]["data"]["groups"]
                    logger.info(f"Successfully retrieved {len(groups)} groups from NextCloud")
                    return groups
                else:
                    logger.error(f"Error listing groups from NextCloud: {resp.status_code} {resp.text}")
                    return []
        except Exception as e:
            logger.error(f"Exception occurred while listing groups from NextCloud: {e}")
            return []
            
    async def list_group_members(self, group: str) -> list[str]:
        logger.info(f"Listing members of group '{group}' from NextCloud")
        try:
            async with httpx.AsyncClient(auth=self.nc_auth) as client:
                resp = await client.get(
                    NC_URL + f"/ocs/v1.php/cloud/groups/{group}",
                    headers=self.api_headers
                )

                if resp.status_code == 200:
                    data = resp.json()
                    users = data["ocs"]["data"]["users"]
                    logger.info(f"Successfully retrieved {len(users)} members for group '{group}'")
                    return users
                else:
                    logger.error(f"Error listing members for group '{group}': {resp.status_code} {resp.text}")
                    return []
        except Exception as e:
            logger.error(f"Exception occurred while listing members for group '{group}': {e}")
            return []
            
    async def get_groups_membership(self) -> dict[str, list[str]]:
        groups_membership = {}
        groups = await self.list_groups()
        for g in groups:
            members = await self.list_group_members(g)
            groups_membership[g] = members
        return groups_membership
    
    async def get_sharees(self, path: str | Path) -> set[str]:
        """Get list of user IDs who have access to the given path."""
        p = Path(path)
        
        if self._is_groupfolder_path(p):
            return await self._get_groupfolder_sharees(p)
        else:
            return await self._get_regular_sharees(p)

    def _is_groupfolder_path(self, path: Path) -> bool:
        """Check if the path is within a groupfolder."""
        path_str = str(path)
        return "__groupfolders" in path_str or any(
            part in ["Dossiers", "dossiers"] for part in path.parts
        )

    async def _get_groupfolder_sharees(self, path: Path) -> set[str]:
        sharees = set()
        
        if not self.usergroups:
            self.usergroups = await self.get_groups_membership()
        
        # First, get the groupfolder info - try index.php endpoint first
        url = NC_URL + "/index.php/apps/groupfolders/folders"
        
        async with httpx.AsyncClient(auth=self.nc_auth) as client:
            resp = await client.get(url, headers=self.api_headers)
            logger.debug(resp.json())
            
            if resp.status_code != 200:
                logger.error(f"Error fetching groupfolders: {resp.status_code} {resp.text}")
                return sharees
            
            payload = resp.json()
            folders = payload.get("ocs", {}).get("data", {})
            
            # Find the relevant groupfolder
            for folder_id, folder_info in folders.items():
                folder_mount_point = folder_info.get("mount_point", "")
                
                # Check if our path is within this groupfolder
                if self._path_matches_groupfolder(path, folder_mount_point):
                    logger.debug(f"Found matching groupfolder {folder_id}: {folder_mount_point}")
                    
                    # Start with folder-level permissions
                    folder_groups = folder_info.get("groups", {})
                    for group_name, _ in folder_groups.items():
                        if group_name in self.usergroups:
                            sharees.update(self.usergroups[group_name])
                            logger.debug(f"Added users from folder-level group {group_name}: {self.usergroups[group_name]}")
                    
                    # Now check for ACL permissions on the specific path
                    acl_sharees = await self._get_groupfolder_acl_sharees(folder_id, path, folder_mount_point)
                    if acl_sharees is not None:
                        logger.debug(f"ACL permissions found, using ACL sharees instead")
                        sharees = acl_sharees
                    else:
                        logger.debug(f"No ACL permissions available, using folder-level permissions")
                    
                    break
    
        return sharees

    def _path_matches_groupfolder(self, path: Path, mount_point: str) -> bool:
        """Check if a path belongs to a specific groupfolder."""
        path_str = str(path).lower()
        mount_point_lower = mount_point.lower()
        
        return (
            mount_point_lower in path_str or
            any(part.lower() == mount_point_lower for part in path.parts)
        )
    
    def _get_permissions(self, permissions: int) -> set[str]:
        """Decode permission integer into a set of permission strings."""
        perm_set = set()
        if permissions & 1:
            perm_set.add("read")
        if permissions & 2:
            perm_set.add("write")
        if permissions & 4:
            perm_set.add("create")
        if permissions & 8:
            perm_set.add("delete")
        if permissions & 16:
            perm_set.add("share")
        if permissions & 32:
            perm_set.add("sync")
        return perm_set

    async def _get_groupfolder_acl_sharees(self, folder_id: str, path: Path, mount_point: str) -> set[str]:
        """Get sharees based on ACL permissions for a specific path in a groupfolder."""
        sharees = set()
        
        # Calculate the relative path within the groupfolder
        relative_path = self._get_relative_path_in_groupfolder(path, mount_point)
        
        if not relative_path:
            return sharees
        
        # First check if ACL is enabled
        folder_url = f"{NC_URL}/index.php/apps/groupfolders/folders/{folder_id}"
        
        async with httpx.AsyncClient(auth=self.nc_auth) as client:
            folder_resp = await client.get(folder_url, headers=self.api_headers)

            if folder_resp.status_code != 200:
                logger.debug(f"Could not fetch folder info for {folder_id}: {folder_resp.status_code}")
                return sharees
            
            folder_data = folder_resp.json()
            folder_info = folder_data.get("ocs", {}).get("data", {})
            acl_enabled = folder_info.get("acl", False)
            
            if not acl_enabled:
                logger.debug(f"ACL not enabled for groupfolder {folder_id}")
                return sharees
            
        xml_body = """<?xml version="1.0"?>
        <d:propfind xmlns:d="DAV:" xmlns:nc="http://nextcloud.org/ns">
        <d:prop>
            <nc:acl-list/>
            <nc:inherited-acl-list/>
            <nc:group-folder-id/>
            <nc:acl-enabled/>
            <nc:acl-can-manage/>
        </d:prop>
        </d:propfind>
        """

        xml_url = self.base_url + f"/remote.php/dav/groupfolders/{path}"
        async with httpx.AsyncClient(auth=self.nc_auth) as client:
            resp = await client.request(
                "PROPFIND", 
                xml_url,
                headers=self.xml_header,
                data=xml_body
            )

        xml_response = resp.content

        # Parse XML response
        ns = {"d": "DAV:", "nc": "http://nextcloud.org/ns"}
        root = ET.fromstring(xml_response)

        # Direct ACLs
        for acl in root.findall(".//nc:acl-list/nc:acl", ns):
            mapping_type = acl.findtext("nc:acl-mapping-type", namespaces=ns)
            if mapping_type == "group":
                group = acl.findtext("nc:acl-mapping-id", namespaces=ns)
                perms = acl.findtext("nc:acl-permissions", namespaces=ns)
                if 'read' in self._get_permissions(int(perms) if perms and perms.isdigit() else 0):
                    for user in self.usergroups.get(group, []):
                        logger.debug(f"Adding user {user} from group {group} based on ACL")
                        sharees.add(user)
            elif mapping_type == "user":
                user = acl.findtext("nc:acl-mapping-id", namespaces=ns)
                perms = acl.findtext("nc:acl-permissions", namespaces=ns)
                if 'read' in self._get_permissions(int(perms) if perms and perms.isdigit() else 0):
                    logger.debug(f"Adding user {user} based on ACL")
                    sharees.add(user)
            else:
                raise ValueError(f"Unsupported ACL mapping type: {mapping_type}")

        # Inherited ACLs
        for acl in root.findall(".//nc:inherited-acl-list/nc:acl", ns):
            mapping_type = acl.findtext("nc:acl-mapping-type", namespaces=ns)
            if mapping_type == "group":
                group = acl.findtext("nc:acl-mapping-id", namespaces=ns)
                perms = acl.findtext("nc:acl-permissions", namespaces=ns)
                if 'read' in self._get_permissions(int(perms) if perms and perms.isdigit() else 0):
                    for user in self.usergroups.get(group, []):
                        logger.debug(f"Adding user {user} from group {group} based on inherited ACL")
                        sharees.add(user)
            elif mapping_type == "user":
                user = acl.findtext("nc:acl-mapping-id", namespaces=ns)
                perms = acl.findtext("nc:acl-permissions", namespaces=ns)
                if 'read' in self._get_permissions(int(perms) if perms and perms.isdigit() else 0):
                    logger.debug(f"Adding user {user} based on inherited ACL")
                    sharees.add(user)
            else:
                raise ValueError(f"Unsupported ACL mapping type: {mapping_type}")
        
        return sharees

    def _get_relative_path_in_groupfolder(self, path: Path, mount_point: str) -> str:
        """Extract the relative path within a groupfolder."""
        path_str = str(path)
        
        if mount_point.lower() in path_str.lower():
            mount_idx = path_str.lower().find(mount_point.lower())
            if mount_idx >= 0:
                start_idx = mount_idx + len(mount_point)
                relative_path = path_str[start_idx:].lstrip("/")
                return relative_path
        
        for i, part in enumerate(path.parts):
            if part.lower() == mount_point.lower():
                if i + 1 < len(path.parts):
                    remaining_parts = path.parts[i + 1:]
                    return "/".join(remaining_parts)
                else:
                    return ""
        
        return ""

    def _find_applicable_acl_rules(self, acl_rules: dict, target_path: str) -> list[dict]:
        """Find ACL rules that apply to the target path."""
        applicable_rules = []
        
        for rule_path, rules in acl_rules.items():
            # Check if the rule path is a parent of or matches the target path
            if self._path_is_applicable(rule_path, target_path):
                if isinstance(rules, list):
                    applicable_rules.extend(rules)
                elif isinstance(rules, dict):
                    applicable_rules.append(rules)
        
        return applicable_rules

    def _path_is_applicable(self, rule_path: str, target_path: str) -> bool:
        """Check if an ACL rule path applies to the target path."""
        if not rule_path or rule_path == "/":
            return True  # Root level rule applies to everything
        
        rule_path = rule_path.strip("/")
        target_path = target_path.strip("/")
        
        # Exact match
        if rule_path == target_path:
            return True
        
        # Rule path is a parent of target path
        if target_path.startswith(rule_path + "/"):
            return True
        
        return False

    async def _get_regular_sharees(self, path: Path) -> set[str]:
        """Get sharees for regular file shares."""
        p = path.relative_to(*path.parts[:2])
        path_str = str(p)

        if not self.usergroups:
            self.usergroups = await self.get_groups_membership()

        # Build list of candidate paths: the path itself + all its parents
        candidates: list[str] = []
        if path_str not in ("", "."):
            candidates.append(path_str)
        for parent in p.parents:
            s = str(parent)
            if s not in ("", "."):
                candidates.append(s)

        unique_candidates = set(candidates)

        sharees = set()
        url = NC_URL + "/ocs/v2.php/apps/files_sharing/api/v1/shares"
        for cand in unique_candidates:
            async with httpx.AsyncClient(auth=self.nc_auth) as client:
                resp = await client.get(
                    url,
                    headers=self.api_headers,
                    params={"path": cand, "reshares": "true", "subfiles": "false"},
                )

            if resp.status_code != 200:
                logger.error(f"Error fetching shares for path {cand}: {resp.status_code} {resp.text}")
                continue

            payload = resp.json()
            data = payload.get("ocs", {}).get("data", [])

            for share in data:
                share_with = share.get("share_with")
                if share_with in self.usergroups:
                    logger.debug(f"Share with group {share_with}, adding members: {self.usergroups[share_with]}")
                    sharees.update(self.usergroups[share_with])
                else:
                    sharees.add(share_with)

        return sharees

    # Activity API methods for incremental updates
    async def get_activities_since(self, since_activity_id: int, limit: int = 1000, retries: int = 3) -> dict:
        """
        Get activities from NextCloud Activity API since a given activity ID.
        
        Args:
            since_activity_id: The ID of the last processed activity
            limit: Maximum number of activities to retrieve (default: 50)
            retries: Number of retry attempts on failure (default: 3)
            
        Returns:
            dict: Activity API response with activities and metadata
        """
        url = f"{NC_URL}/ocs/v2.php/apps/activity/api/v2/activity"
        params = {
            "since": since_activity_id,
            "limit": limit,
            "sort": "asc",  # Get activities in ascending order for proper processing
            # Removed "object_type": "files" filter as it excludes grouped activities
        }
        
        auth = (NC_USER, NC_PASSWORD)
        
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(auth=auth, timeout=30.0) as client:
                    resp = await client.get(url, headers=self.api_headers, params=params)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        activities = data.get("ocs", {}).get("data", [])
                        logger.info(f"Retrieved {len(activities)} activities since ID {since_activity_id}")
                        return data
                    elif resp.status_code == 204:
                        logger.info("No new activities found")
                        return {"ocs": {"data": []}}
                    elif resp.status_code == 304:
                        logger.info("No new activities (304 Not Modified)")
                        return {"ocs": {"data": []}}
                    else:
                        logger.warning(f"Activity API returned status {resp.status_code}: {resp.text}")
                        
                        # Don't retry on client errors (4xx)
                        if 400 <= resp.status_code < 500:
                            raise Exception(f"Client error from Activity API: {resp.status_code} {resp.text}")
                            
            except Exception as e:
                logger.warning(f"Activity API attempt {attempt + 1}/{retries + 1} failed: {e}")
                if attempt == retries:
                    logger.error(f"Activity API failed after {retries + 1} attempts: {e}")
                    raise Exception(f"Failed to get activities after {retries + 1} attempts: {e}")
                    
                # Wait before retrying (exponential backoff)
                import asyncio
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Unexpected error in activity retrieval")

    async def get_latest_activity_id(self, retries: int = 3) -> int:
        """
        Get the latest (highest) activity ID from NextCloud Activity API.
        
        Args:
            retries: Number of retry attempts on failure (default: 3)
            
        Returns:
            int: The highest activity ID, or 0 if no activities found
        """
        url = f"{NC_URL}/ocs/v2.php/apps/activity/api/v2/activity"
        params = {
            "since": 0,
            "limit": 1,
            "sort": "desc",  # Get activities in descending order to get latest first
            # Removed "object_type": "files" filter as it excludes grouped activities
        }
        
        auth = (NC_USER, NC_PASSWORD)
        
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(auth=auth, timeout=30.0) as client:
                    resp = await client.get(url, headers=self.api_headers, params=params)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        activities = data.get("ocs", {}).get("data", [])
                        if activities:
                            latest_id = activities[0].get("activity_id", 0)
                            logger.info(f"Latest activity ID: {latest_id}")
                            return latest_id
                        else:
                            logger.info("No activities found")
                            return 0
                    elif resp.status_code == 204:
                        logger.info("No activities found")
                        return 0
                    elif resp.status_code == 304:
                        logger.info("No activities found (304 Not Modified)")
                        return 0
                    else:
                        logger.warning(f"Activity API returned status {resp.status_code}: {resp.text}")
                        
                        # Don't retry on client errors (4xx)
                        if 400 <= resp.status_code < 500:
                            raise Exception(f"Client error from Activity API: {resp.status_code} {resp.text}")
                            
            except Exception as e:
                logger.warning(f"Latest activity ID attempt {attempt + 1}/{retries + 1} failed: {e}")
                if attempt == retries:
                    logger.error(f"Failed to get latest activity ID after {retries + 1} attempts: {e}")
                    return 0  # Return 0 as fallback instead of raising
                    
                # Wait before retrying (exponential backoff)
                import asyncio
                await asyncio.sleep(2 ** attempt)
        
        return 0  # Fallback

    async def filter_file_activities(self, activities: list[dict]) -> list[dict]:
        """
        Filter activities to only include file/folder related ones we care about.
        
        Args:
            activities: List of activity objects from the API
            
        Returns:
            list: Filtered activities for files/folders we need to process
        """
        relevant_types = {
            "file_created", "file_changed", "file_deleted", 
            "file_moved", "file_renamed", "folder_created",
            "folder_deleted", "folder_moved", "folder_renamed"
        }
        
        relevant_apps = {"files", "files_sharing"}
        
        filtered = []
        for activity in activities:
            activity_type = activity.get("type", "")
            activity_app = activity.get("app", "")
            object_type = activity.get("object_type", "")
            object_name = activity.get("object_name", "")
            
            # Must be file/folder related
            if object_type != "files":
                continue
                
            # Must be from relevant apps
            if activity_app not in relevant_apps:
                continue
                
            # Must be relevant activity type (or if unknown, include it to be safe)
            if activity_type and activity_type not in relevant_types:
                logger.debug(f"Skipping activity type '{activity_type}' for {object_name}")
                continue
                
            # Must have a valid object_name (file path)
            if not object_name:
                logger.debug(f"Skipping activity without object_name: {activity}")
                continue
                
            filtered.append(activity)
            logger.debug(f"Including activity: {activity_type} on {object_name}")
            
        logger.info(f"Filtered {len(filtered)} relevant file activities from {len(activities)} total")
        return filtered

    async def extract_file_paths_from_activities(self, activities: list[dict]) -> dict[str, set[str]]:
        """
        Extract file paths from activities and categorize them by action type.
        Handles grouped activities where multiple files are created in a single activity (common with WebDAV uploads).
        
        Args:
            activities: List of filtered activity objects
            
        Returns:
            dict: Categorized file paths {"created": set, "updated": set, "deleted": set}
        """
        created_files = set()
        updated_files = set()
        deleted_files = set()
        
        for activity in activities:
            activity_type = activity.get("type", "")
            object_name = activity.get("object_name", "")
            objects = activity.get("objects", {})
            
            # Extract all file paths from this activity
            file_paths = set()
            
            # First, check if there are multiple objects (grouped activity)
            if objects and isinstance(objects, dict):
                for obj_id, obj_path in objects.items():
                    if obj_path and isinstance(obj_path, str):
                        # Normalize the path (remove leading slash if present)
                        normalized_path = obj_path.lstrip("/")
                        file_paths.add(normalized_path)
                        logger.debug(f"Found object in grouped activity: {normalized_path}")
            
            # If no objects found, fall back to object_name
            if not file_paths and object_name:
                normalized_path = object_name.lstrip("/")
                file_paths.add(normalized_path)
                logger.debug(f"Using object_name: {normalized_path}")
            
            # Also check subject_rich for additional file information
            subject_rich = activity.get("subject_rich", [])
            if isinstance(subject_rich, list) and len(subject_rich) > 1:
                rich_objects = subject_rich[1]
                if isinstance(rich_objects, dict):
                    for key, obj_data in rich_objects.items():
                        if isinstance(obj_data, dict) and "path" in obj_data:
                            path = obj_data["path"].lstrip("/")
                            file_paths.add(path)
                            logger.debug(f"Found path in subject_rich: {path}")
            
            if not file_paths:
                logger.debug(f"No file paths found in activity: {activity}")
                continue
            
            # Categorize all found paths based on activity type
            for file_path in file_paths:
                # Skip directory paths - only process actual files
                # Directories typically don't have extensions and end with folder names
                if self._is_likely_file(file_path):
                    if activity_type in {"file_created", "folder_created"}:
                        created_files.add(file_path)
                        logger.debug(f"Added to created: {file_path}")
                    elif activity_type in {"file_changed"}:
                        updated_files.add(file_path)
                        logger.debug(f"Added to updated: {file_path}")
                    elif activity_type in {"file_deleted", "folder_deleted"}:
                        deleted_files.add(file_path)
                        logger.debug(f"Added to deleted: {file_path}")
                    elif activity_type in {"file_moved", "file_renamed", "folder_moved", "folder_renamed"}:
                        # For moved/renamed files, treat as both delete (old path) and create (new path)
                        created_files.add(file_path)
                        logger.debug(f"Added to created (moved): {file_path}")
                        
                        # Try to extract old path from subject_rich or other fields
                        # This might need refinement based on actual API response format
                        subject_rich = activity.get("subject_rich", {})
                        if isinstance(subject_rich, dict) and len(subject_rich) > 1:
                            rich_objects = subject_rich.get("1", {})
                            if isinstance(rich_objects, dict):
                                for key, obj_data in rich_objects.items():
                                    if isinstance(obj_data, dict) and "path" in obj_data:
                                        old_path = obj_data["path"].lstrip("/")
                                        if old_path != file_path:
                                            deleted_files.add(old_path)
                                            logger.debug(f"Move/rename: {old_path} -> {file_path}")
                    else:
                        # Default to updated for unknown types
                        logger.debug(f"Unknown activity type '{activity_type}', treating as updated: {file_path}")
                        updated_files.add(file_path)
                else:
                    logger.debug(f"Skipping directory path: {file_path}")
        
        logger.info(f"Extracted paths - Created: {len(created_files)}, Updated: {len(updated_files)}, Deleted: {len(deleted_files)}")
        
        return {
            "created": created_files,
            "updated": updated_files,
            "deleted": deleted_files
        }
    
    def _is_likely_file(self, path: str) -> bool:
        """
        Determine if a path is likely a file (vs a directory).
        
        Args:
            path: The file path to check
            
        Returns:
            bool: True if likely a file, False if likely a directory
        """
        import os
        
        # If path has a file extension, it's likely a file
        _, ext = os.path.splitext(path)
        if ext:
            return True
            
        # If path ends with a known file pattern without extension
        # (like README, Makefile, etc.), consider it a file
        filename = os.path.basename(path).lower()
        extensionless_files = {'readme', 'makefile', 'dockerfile', 'license', 'changelog'}
        if filename in extensionless_files:
            return True
            
        # Otherwise, assume it's a directory
        return False
    
    async def get_last_modified_user_async(self, fileID: str) -> str | None:
        """
        Get the username of the last user who modified a Nextcloud file.
        """
        headers = {"OCS-APIRequest": "true"}

        async with httpx.AsyncClient(auth=self.nc_auth, headers=headers, timeout=15.0) as client:
            activity_url = f"{NC_URL}/ocs/v2.php/apps/activity/api/v2/activity/filter"
            params = {"format": "json", "object_type": "files", "object_id": fileID}

            resp = await client.get(activity_url, params=params)
            resp.raise_for_status()

            data = resp.json()
            activities = data.get("ocs", {}).get("data", [])

            # Step 3: Find the most recent modification activity
            for event in sorted(activities, key=lambda x: x.get("timestamp", 0), reverse=True):
                if event.get("type") in ("file_changed", "file_created"):
                    return event.get("user")

        return None


    async def get_folder_file_id_simple(self, folder_path: str) -> str | None:
        """
        Get the file ID for a folder using the Files API.
        This method uses the same API that the Activity API references.
        
        Args:
            folder_path: The path to the folder (e.g., "/Dossiers/SomeFolderName")
            
        Returns:
            str | None: The file ID if found, None otherwise
        """
        try:
            # Try the OCS Files API to get folder info
            # This is similar to what the Activity API references
            url = f"{NC_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares"
            
            # Alternative: try the WebDAV PROPFIND with different properties
            xml_body = """<?xml version="1.0"?>
            <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
            <d:prop>
                <oc:fileid/>
                <oc:id/>
                <nc:id/>
                <d:resourcetype/>
            </d:prop>
            </d:propfind>
            """

            webdav_url = self.webdavclient.get_url(folder_path)
            resp = self.webdavclient.session.request(
                "PROPFIND",
                webdav_url,
                auth=self.nc_auth,
                headers=self.xml_header,
                data=xml_body
            )
            resp.raise_for_status()

            # Parse the response and look for any ID field
            ns = {"d": "DAV:", "oc": "http://owncloud.org/ns", "nc": "http://nextcloud.org/ns"}
            root = ET.fromstring(resp.content)
            
            logger.debug(f"WebDAV response for {folder_path}: {resp.content.decode('utf-8')}")
            
            # Try multiple possible ID fields
            for id_field in [".//oc:fileid", ".//oc:id", ".//nc:id"]:
                id_elem = root.find(id_field, ns)
                if id_elem is not None and id_elem.text:
                    logger.info(f"Found folder ID {id_elem.text} for {folder_path} using {id_field}")
                    return id_elem.text
            
            logger.warning(f"No ID found in WebDAV response for {folder_path}")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get folder file_id using simple method for {folder_path}: {e}")
            return None


    async def get_folder_file_id_from_activity(self, folder_path: str, retries: int = 3) -> str | None:
        """
        Get the file ID for a folder by looking for it in recent activity API data.
        This is more reliable than WebDAV for some Nextcloud configurations.
        
        Args:
            folder_path: The path to the folder (e.g., "/Dossiers/SomeFolderName")
            retries: Number of retry attempts
            
        Returns:
            str | None: The file ID if found, None otherwise
        """
        try:
            # Get recent activities to find the folder
            activity_data = await self.get_activities_since(0, limit=1000)
            activities = activity_data.get("ocs", {}).get("data", [])
            
            # Normalize the folder path for comparison
            normalized_folder_path = folder_path.strip('/')
            logger.debug(f"Looking for folder: {normalized_folder_path}")
            
            for activity in activities:
                logger.debug(f"Checking activity {activity.get('activity_id')}: {activity.get('type')}")
                
                # Method 1: Check subject_rich for exact folder matches
                subject_rich = activity.get("subject_rich", [])
                if len(subject_rich) > 1 and isinstance(subject_rich[1], dict):
                    for key, obj in subject_rich[1].items():
                        if isinstance(obj, dict):
                            obj_path = obj.get("path", "").strip('/')
                            obj_id = obj.get("id")
                            obj_type = obj.get("type", "")
                            
                            logger.debug(f"  Found object: path={obj_path}, id={obj_id}, type={obj_type}")
                            
                            # Check if this object represents our folder exactly
                            if obj_path == normalized_folder_path and obj_id:
                                logger.info(f"Found exact folder match: ID {obj_id} for {folder_path}")
                                return obj_id
                            
                            # Check if this is a file in our target folder
                            if obj_path.startswith(normalized_folder_path + "/") and obj_type == "file":
                                logger.debug(f"Found file in target folder: {obj_path}")
                                # Continue looking for the folder itself
                
                # Method 2: Check if object_name references our folder
                object_name = activity.get("object_name", "")
                if object_name and normalized_folder_path in object_name:
                    logger.debug(f"  Activity object_name contains our folder: {object_name}")
                    
                    # Check if object_id might be our folder ID
                    object_id = activity.get("object_id")
                    if object_id:
                        logger.debug(f"  Found potential folder ID from object_id: {object_id}")
                        # We could return this, but let's be more cautious and continue looking
                
                # Method 3: Check objects field for any files in our folder
                objects = activity.get("objects", {})
                if objects:
                    for file_id, path in objects.items():
                        normalized_path = path.strip('/')
                        logger.debug(f"  Found object: file_id={file_id}, path={normalized_path}")
                        
                        # If this file is directly in our target folder
                        if normalized_path.startswith(normalized_folder_path + "/"):
                            # This confirms our folder exists, but we still need the folder ID
                            # For now, let's continue looking for a better match
                            pass
                
                # Method 4: Check activity link for folder references
                link = activity.get("link", "")
                if link and (f"dir=/{normalized_folder_path}" in link or 
                           f"dir=%2F{normalized_folder_path.replace('/', '%2F')}" in link):
                    logger.debug(f"  Activity link references our folder: {link}")
                    # This confirms the folder exists but doesn't give us the ID directly
            
            logger.info(f"No file_id found for folder {folder_path} in activity data")
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get folder file_id from activity API for {folder_path}: {e}")
            return None
