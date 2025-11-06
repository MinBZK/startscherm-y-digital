/**
 * Utility functions for handling Nextcloud URLs and transformations
 */

/**
 * Transform a webURL from Elasticsearch format to proper Nextcloud file browser URL
 * @param webURL - The webURL from ES index (e.g., "/Dossiers/Klacht_Woo_Verzoek_Jan_de_Vries")
 * @param fileId - The Nextcloud file ID for the dossier folder (optional, will use default if not provided)
 * @param nextcloudBaseUrl - The base URL of the Nextcloud instance
 * @returns Properly formatted Nextcloud URL
 */
export function transformToNextcloudUrl(
  webURL: string,
  fileId?: string,
  nextcloudBaseUrl?: string
): string {
  // Get the Nextcloud base URL from environment or use default
  const baseUrl = nextcloudBaseUrl || 
    process.env.NEXT_PUBLIC_NEXTCLOUD_BASE_URL || 
    'http://localhost:8080';

  // Use the provided file ID or a default one
  // Note: In a real scenario, this should be retrieved from the backend
  const defaultFileId = '157'; // This should come from the API response
  const actualFileId = fileId || defaultFileId;

  // Use the new Nextcloud URL format: /index.php/f/{file_id}
  const nextcloudUrl = `${baseUrl}/index.php/f/${actualFileId}`;

  return nextcloudUrl;
}

/**
 * Extract the dossier name from a webURL path
 * @param webURL - The webURL path (e.g., "/Dossiers/Klacht_Woo_Verzoek_Jan_de_Vries")
 * @returns The dossier name
 */
export function extractDossierName(webURL: string): string {
  const parts = webURL.split('/').filter(part => part.length > 0);
  // Assuming the structure is /Dossiers/{DOSSIER_NAME}
  return parts.length >= 2 ? parts[1] : '';
}

/**
 * Check if a URL is a dossier URL based on its path structure
 * @param webURL - The webURL to check
 * @returns True if it appears to be a dossier URL
 */
export function isDossierUrl(webURL: string): boolean {
  const normalizedPath = webURL.toLowerCase();
  return normalizedPath.includes('/dossiers/') || normalizedPath.startsWith('dossiers/');
}