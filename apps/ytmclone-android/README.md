# YTMClone Android

Native Android wrapper for the real YouTube Music web surface. The signed-in YouTube Music account remains the playback brain for recommendations, mixes, likes, playlists, queue, Premium behavior, and normal play order. YTMClone adds a native shell and tracking bridge that sends song/session events to SpiritOS.

## What this builds

- Kotlin + Jetpack Compose Android app.
- Persistent WebView loading `https://music.youtube.com`.
- JavaScript `MutationObserver` bridge for now-playing, playback state, position/duration, source URL, thumbnail, and video ID when visible.
- Native queued event delivery to SpiritOS.
- In-app SpiritOS backend URL setting.
- `/stats` action that opens the SpiritOS stats page.
- Diagnostics menu with notification-listener fallback and official YouTube Music open action.

This app does not extract audio, download audio, bypass ads, bypass DRM, or replace YouTube Music's visible playback experience.

## Build from the Dell

From the repo root:

```bash
cd /home/source/SpiritOS
npm run ytmclone:android:build
```

Equivalent direct command:

```bash
cd /home/source/SpiritOS/apps/ytmclone-android
./gradlew assembleDebug
```

Expected APK:

```text
/home/source/SpiritOS/apps/ytmclone-android/app/build/outputs/apk/debug/app-debug.apk
```

This shell needs a JDK and Android SDK first:

```bash
java -version
echo "$ANDROID_HOME"
```

The project expects:

- JDK 17 or newer available as `java`.
- Android SDK with platform 35 and build-tools installed.
- `ANDROID_HOME` or `ANDROID_SDK_ROOT` pointed at that SDK.

One command-line bootstrap path on Ubuntu/Debian is:

```bash
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk unzip
mkdir -p "$HOME/Android/Sdk/cmdline-tools"
cd /tmp
curl -LO https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip commandlinetools-linux-11076708_latest.zip
mkdir -p "$HOME/Android/Sdk/cmdline-tools/latest"
mv cmdline-tools/* "$HOME/Android/Sdk/cmdline-tools/latest/"
export ANDROID_HOME="$HOME/Android/Sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
yes | sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-35" "build-tools;35.0.0"
```

After that, rerun:

```bash
cd /home/source/SpiritOS/apps/ytmclone-android
./gradlew assembleDebug
```

## Install on Samsung Fold 7

If `adb` is available and the phone is connected with USB debugging:

```bash
adb devices
adb install -r /home/source/SpiritOS/apps/ytmclone-android/app/build/outputs/apk/debug/app-debug.apk
```

If `adb` is not available, copy the APK to the phone after building it, open it from Files, and allow install from that source when Android prompts.

## First run

1. Open YTMClone.
2. Sign into YouTube Music in the embedded web surface if prompted.
3. Tap `URL` and set the SpiritOS backend to the Dell LAN URL, for example `http://192.168.1.50:3000`.
4. Start playback inside the visible YouTube Music surface.
5. Open `http://DELL_LAN_IP:3000/stats` or tap `Stats`.

## Notification fallback

Use this only if Google blocks embedded sign-in or the WebView cannot expose useful now-playing data.

1. Install the official YouTube Music app and sign into the same Premium account.
2. In YTMClone, tap `Diag`.
3. Tap `Notification Access`.
4. Enable `YTMClone playback tracker`.
5. Play music in the official YouTube Music app.

The fallback reads notification metadata with your permission and sends it to SpiritOS. It does not control, download, rip, or modify YouTube Music playback.
