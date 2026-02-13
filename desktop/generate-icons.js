/**
 * Generate platform-specific icons from SVG source
 * Creates .ico (Windows), .icns (macOS), and .png (Linux) formats
 */

const sharp = require('sharp');
const { default: pngToIco } = require('png-to-ico');
const fs = require('fs');
const path = require('path');

const ASSETS_DIR = path.join(__dirname, 'assets');
const SOURCE_IMAGE = path.join(ASSETS_DIR, 'handbell-icon-full-cropped.png');

// Icon sizes needed for different platforms
const SIZES = {
  windows: [16, 24, 32, 48, 64, 128, 256],  // For ICO
  mac: [16, 32, 64, 128, 256, 512, 1024],    // For ICNS
  linux: [512]                                // Main PNG
};

async function generateIcons() {
  console.log('🎨 Generating application icons...\n');

  try {
    // Create temporary directory for PNGs
    const tempDir = path.join(ASSETS_DIR, 'temp');
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }

    // Path to frontend public directory (used multiple times)
    const frontendPublic = path.join(__dirname, '..', 'frontend', 'public');

    // 1. Generate Windows ICO
    console.log('📦 Generating Windows icon (icon.ico)...');
    const windowsPngs = [];
    for (const size of SIZES.windows) {
      const pngPath = path.join(tempDir, `icon-${size}.png`);
      await sharp(SOURCE_IMAGE)
        .resize(size, size)
        .png()
        .toFile(pngPath);
      windowsPngs.push(pngPath);
    }
    
    const icoBuffer = await pngToIco(windowsPngs);
    fs.writeFileSync(path.join(ASSETS_DIR, 'icon.ico'), icoBuffer);
    console.log('✓ Created icon.ico with sizes:', SIZES.windows.join(', '));

    // 1.5. Generate web favicon.ico (16x16, 32x32, 48x48)
    console.log('\n🌐 Generating web favicon (favicon.ico)...');
    const faviconPngs = [16, 32, 48].map(size => {
      return path.join(tempDir, `icon-${size}.png`);
    });
    const faviconBuffer = await pngToIco(faviconPngs);
    fs.writeFileSync(path.join(frontendPublic, 'favicon.ico'), faviconBuffer);
    console.log('✓ Created favicon.ico for web app (16, 32, 48)');

    // 2. Generate macOS PNG (icns conversion needs external tool)
    console.log('\n📦 Generating macOS icons (PNG set for ICNS)...');
    const macIconSet = path.join(ASSETS_DIR, 'icon.iconset');
    if (!fs.existsSync(macIconSet)) {
      fs.mkdirSync(macIconSet, { recursive: true });
    }
    
    for (const size of SIZES.mac) {
      await sharp(SOURCE_IMAGE)
        .resize(size, size)
        .png()
        .toFile(path.join(macIconSet, `icon_${size}x${size}.png`));
      
      // Also generate @2x versions for Retina displays
      if (size <= 512) {
        await sharp(SOURCE_IMAGE)
          .resize(size * 2, size * 2)
          .png()
          .toFile(path.join(macIconSet, `icon_${size}x${size}@2x.png`));
      }
    }
    console.log('✓ Created PNG set for macOS');
    console.log('  Note: Run "iconutil -c icns assets/icon.iconset" on macOS to create .icns');

    // 3. Generate Linux PNG
    console.log('\n📦 Generating Linux icon (icon.png)...');
    await sharp(SOURCE_IMAGE)
      .resize(512, 512)
      .png()
      .toFile(path.join(ASSETS_DIR, 'icon.png'));
    console.log('✓ Created icon.png (512x512)');

    // 4. Generate additional sizes for documentation
    console.log('\n📦 Generating additional formats...');
    await sharp(SOURCE_IMAGE)
      .resize(256, 256)
      .png()
      .toFile(path.join(ASSETS_DIR, 'icon-256.png'));
    console.log('✓ Created icon-256.png (for README)');

    await sharp(SOURCE_IMAGE)
      .resize(128, 128)
      .png()
      .toFile(path.join(ASSETS_DIR, 'icon-128.png'));
    console.log('✓ Created icon-128.png (for documentation)');

    // 5. Generate web app icons (192x192 and 512x512 for PWA manifest)
    console.log('\n🌐 Generating web app icons...');
    
    await sharp(SOURCE_IMAGE)
      .resize(192, 192)
      .png()
      .toFile(path.join(frontendPublic, 'logo192.png'));
    console.log('✓ Created logo192.png for web app');
    
    await sharp(SOURCE_IMAGE)
      .resize(512, 512)
      .png()
      .toFile(path.join(frontendPublic, 'logo512.png'));
    console.log('✓ Created logo512.png for web app');

    // Cleanup temp directory
    fs.rmSync(tempDir, { recursive: true, force: true });

    console.log('\n✨ Icon generation complete!');
    console.log('\nGenerated files:');
    console.log('  - assets/icon.ico (Windows)');
    console.log('  - assets/icon.iconset/ (macOS - needs iconutil)');
    console.log('  - assets/icon.png (Linux)');
    console.log('  - assets/icon-256.png (Documentation)');
    console.log('  - assets/icon-128.png (Documentation)');
    console.log('  - ../frontend/public/favicon.ico (Web favicon)');
    console.log('  - ../frontend/public/logo192.png (Web app icon)');
    console.log('  - ../frontend/public/logo512.png (Web app icon)');

  } catch (error) {
    console.error('❌ Error generating icons:', error);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  generateIcons();
}

module.exports = { generateIcons };
