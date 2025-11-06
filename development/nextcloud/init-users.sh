#!/bin/bash

# script for nextcloud to run at startup: creates some default user accounts

set -e

# Wait for Nextcloud to be ready
until php /var/www/html/occ status | grep -q "installed"; do
  sleep 5
done

# Function to run commands as www-data user
run_as_www_data() {
    if [ "$(id -u)" = 0 ]; then
        su -p www-data -s /bin/sh -c "$1"
    else
        sh -c "$1"
    fi
}

create_user() {
    local username="$1"
    local password="$2"
    if ! run_as_www_data "php /var/www/html/occ user:info $username" >/dev/null 2>&1; then
        echo "Creating user $username..."
        run_as_www_data "OC_PASS=$password php /var/www/html/occ user:add --password-from-env $username"
    else
        echo "User $username already exists, skipping..."
    fi
}

install_app() {
    local app="$1"
    if ! run_as_www_data "php /var/www/html/occ app:list" | grep -q "$app: enabled"; then
        echo "Installing/enabling app $app..."
        run_as_www_data "php /var/www/html/occ app:install $app || true"
        run_as_www_data "php /var/www/html/occ app:enable $app"
    else
        echo "App $app already enabled, skipping..."
    fi
}

create_group() {
    local group="$1"
    if run_as_www_data "php /var/www/html/occ group:info $group" >/dev/null 2>&1; then
        echo "Group $group already exists, skipping..."
    else
        echo "Creating group $group..."
        if ! run_as_www_data "php /var/www/html/occ group:add $group"; then
            echo "Group $group creation reported an error (possibly already exists), continuing..."
        fi
    fi
}

add_user_to_group() {
    local user="$1"
    local group="$2"
    if ! run_as_www_data "php /var/www/html/occ group:list-members $group" 2>/dev/null | grep -Fx "$user" >/dev/null; then
        echo "Adding user $user to group $group..."
        run_as_www_data "php /var/www/html/occ group:adduser $group $user"
    else
        echo "User $user already in group $group, skipping..."
    fi
}

# Central occ command variable
OCC="php /var/www/html/occ"

create_groupfolder() {
    local name="$1"
    local id=""
    id=$(run_as_www_data "$OCC groupfolders:list" 2>/dev/null | awk -F'|' -v n=\"$name\" '
        {
            for(i=1;i<=NF;i++){gsub(/^[ \t]+|[ \t]+$/, "", $i)}
            if($0 ~ /\|/ && $2 ~ /^[0-9]+$/){
                if($3 == n){ print $2 }
            }
        }')
    if [ -n "$id" ]; then
        echo "Group folder $name already exists with ID $id, updating permissions/groups..." >&2
    else
        echo "Creating group folder $name..." >&2
        id=$(run_as_www_data "$OCC groupfolders:create \"$name\"" | awk 'NF{print $NF}')
        echo "Created folder $name with ID $id" >&2
    fi
    echo "Setting base group permissions for folder $name (ID $id)..." >&2
    # Grant full permissions (read write delete share) to admin
    run_as_www_data "$OCC groupfolders:group $id admin read write delete share" >/dev/null || echo "Warning: failed setting admin permissions" >&2
    # Read-write for common (if group exists)
    if run_as_www_data "$OCC group:info common" >/dev/null 2>&1; then
        run_as_www_data "$OCC groupfolders:group $id common read write" >/dev/null || echo "Warning: failed setting common permissions" >&2
    fi
    # Return only the ID to stdout
    echo "$id"
}

# Create some default non-admin users
create_user "alice" "SecureAlice2025!"
create_user "bob" "SecureBob2025@"
create_user "charlie" "SecureCharlie2025#"

# Install groupfolders app and setup shared folder
install_app "groupfolders"
create_group "common"
add_user_to_group "alice" "common"
add_user_to_group "bob" "common"
add_user_to_group "charlie" "common"
create_group "team1"
add_user_to_group "alice" "team1"
add_user_to_group "bob" "team1"

# Create Dossiers groupfolder and immediately use returned ID
DOSSIERS_ID=$(create_groupfolder "Dossiers")
echo "Using Dossiers groupfolder ID: $DOSSIERS_ID"

# Create subdirectories (no re-lookup)
run_as_www_data "mkdir -p /var/www/html/data/__groupfolders/$DOSSIERS_ID/Dossier1"
run_as_www_data "mkdir -p /var/www/html/data/__groupfolders/$DOSSIERS_ID/Dossier2"

# Rescan (prefer groupfolders:scan, fallback to files:scan)
if run_as_www_data "$OCC list" 2>&1 | grep -q groupfolders:scan; then
    run_as_www_data "$OCC groupfolders:scan $DOSSIERS_ID" || echo "Warning: groupfolders:scan failed"
else
    run_as_www_data "$OCC files:scan --path=\"__groupfolders/$DOSSIERS_ID\"" || echo "Warning: files:scan failed"
fi

# Enable global ACL if not enabled
if ! run_as_www_data "$OCC config:app:get groupfolders enable_acl" 2>/dev/null | grep -Eq '^(yes|1)$'; then
    run_as_www_data "$OCC config:app:set groupfolders enable_acl --value yes" || echo "Warning: could not set enable_acl"
fi

# Enable per-folder ACL and set rules
run_as_www_data "$OCC groupfolders:permissions $DOSSIERS_ID --enable" || echo "Warning: could not enable ACL on folder"
run_as_www_data "$OCC groupfolders:permissions $DOSSIERS_ID --group team1 /Dossier1 -- +read +write +create +delete +share" || echo "Warn: team1 ACL failed"
run_as_www_data "$OCC groupfolders:permissions $DOSSIERS_ID --group common /Dossier2 -- +read +write -create -delete -share" || echo "Warn: common ACL failed"

echo "User initialization completed."
