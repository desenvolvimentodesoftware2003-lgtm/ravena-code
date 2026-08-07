# MobCrypt ProGuard Rules

# Keep ML Kit barcode scanning
-keep class com.google.mlkit.vision.barcode.** { *; }
-keep class com.google.mlkit.vision.common.** { *; }

# Keep CameraX
-keep class androidx.camera.** { *; }

# Keep Tor related classes
-keep class com.mobcrypt.tor.** { *; }
-keep class com.mobcrypt.vpn.** { *; }

# Keep data classes
-keep class com.mobcrypt.** { *; }
