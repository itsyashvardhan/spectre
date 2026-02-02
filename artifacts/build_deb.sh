#!/bin/bash
set -e

# Configuration
APP_NAME="spectral-tui"
VERSION="1.0.2"
ARCH="all"
BUILD_DIR="build_workspace"
DEB_NAME="${APP_NAME}_${VERSION}_${ARCH}.deb"

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/$APP_NAME"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/doc/$APP_NAME"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/512x512/apps"

echo ">>> Setting up build structure..."

# 1. Copy Core Files
cp ../spectral.py "$BUILD_DIR/usr/lib/$APP_NAME/"
cp ../spectral.png "$BUILD_DIR/usr/lib/$APP_NAME/"
chmod +x "$BUILD_DIR/usr/lib/$APP_NAME/spectral.py"

# 2. Create Launcher Script
cat <<EOF > "$BUILD_DIR/usr/bin/$APP_NAME"
#!/bin/bash
exec python3 /usr/lib/$APP_NAME/spectral.py "\$@"
EOF
chmod +x "$BUILD_DIR/usr/bin/$APP_NAME"

# 3. Create Desktop Entry
# We use the existing one but SED the paths
sed 's|Exec=spectral|Exec=/usr/bin/spectral|g' ../spectral.desktop > "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop"
# Update Icon path
sed -i 's|Icon=.*|Icon=/usr/lib/spectral/spectral.png|g' "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop"

# 4. Create Control File
# Calculate installed size in KB
INSTALLED_SIZE=$(du -sk "$BUILD_DIR/usr" | cut -f1)

cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3
Installed-Size: $INSTALLED_SIZE
Homepage: https://github.com/itsyashvardhan/spectral-tui
Maintainer: itsyashvardhan <itsyashvardhan@users.noreply.github.com>
Description: Advanced System Interface & Dashboard
 A TUI-based dashboard for system monitoring, network scanning,
 and filesystem browsing. Features a minimalist, high-performance
 interface for system operators.
EOF

# 5. Create Copyright File (Fixes 'Unknown License')
mkdir -p "$BUILD_DIR/usr/share/doc/$APP_NAME"
cat <<EOF > "$BUILD_DIR/usr/share/doc/$APP_NAME/copyright"
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: $APP_NAME
Source: https://github.com/itsyashvardhan/spectral-tui

Files: *
Copyright: 2024 itsyashvardhan
License: MIT

License: MIT
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.
EOF

# 6. Install Icon to proper path (Fixes generic icon)
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/512x512/apps"
cp ../spectral.png "$BUILD_DIR/usr/share/icons/hicolor/512x512/apps/spectral.png"

# 7. Create AppStream Metadata (Fixes GUI store details)
mkdir -p "$BUILD_DIR/usr/share/metainfo"
cat <<EOF > "$BUILD_DIR/usr/share/metainfo/spectre.appdata.xml"
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>dev.yashvs.spectral-tui</id>
  <metadata_license>MIT</metadata_license>
  <project_license>MIT</project_license>
  <name>Spectral</name>
  <summary>Advanced System Interface &amp; Dashboard</summary>
  <description>
    <p>A minimalist, high-performance system interface designed for operators who value speed and aesthetics.</p>
    <ul>
      <li>Real-time system telemetry</li>
      <li>Integrated file browser with previews</li>
      <li>Embedded terminal for direct OS commands</li>
    </ul>
  </description>
  <launchable type="desktop-id">spectral.desktop</launchable>
  <url type="homepage">https://github.com/itsyashvardhan/spectral-tui</url>
  <developer_name>itsyashvardhan</developer_name>
  <screenshots>
    <screenshot type="default">
      <caption>The main Spectral dashboard showing system stats.</caption>
      <image>https://raw.githubusercontent.com/itsyashvardhan/spectral-tui/main/spectral.png</image>
    </screenshot>
  </screenshots>
  <releases>
    <release version="1.0.2" date="2026-02-02">
      <description>
        <p>Rebranding to Spectral with updated interface and documentation.</p>
      </description>
    </release>
    <release version="1.0.1" date="2026-01-27">
      <description>
        <p>Improved package metadata for better integration with Linux App Stores.</p>
      </description>
    </release>
  </releases>
</component>
EOF

# 8. Build
echo ">>> Building .deb package..."
mkdir -p ../releases
dpkg-deb --build "$BUILD_DIR" "../releases/$DEB_NAME"

echo ">>> Build Complete: releases/$DEB_NAME"
ls -lh "../releases/$DEB_NAME"
