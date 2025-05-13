import os
import tempfile
import subprocess
import shutil
import sys

def create_android_app(app_name, html_file, python_entry_point):
    temp_dir = tempfile.mkdtemp()
    print(f"[*] Created temporary directory: {temp_dir}")

    assets_dir = os.path.join(temp_dir, 'app', 'src', 'main', 'assets')
    java_dir = os.path.join(temp_dir, 'app', 'src', 'main', 'java', 'com', 'example', app_name.lower())
    res_dir = os.path.join(temp_dir, 'app', 'src', 'main', 'res')

    os.makedirs(assets_dir, exist_ok=True)
    os.makedirs(java_dir, exist_ok=True)
    os.makedirs(os.path.join(res_dir, 'layout'), exist_ok=True)
    os.makedirs(os.path.join(res_dir, 'values'), exist_ok=True)

    shutil.copy(html_file, os.path.join(assets_dir, 'index.html'))

    with open(os.path.join(temp_dir, 'app', 'src', 'main', 'AndroidManifest.xml'), 'w') as f:
        f.write("""<manifest xmlns:android=\"http://schemas.android.com/apk/res/android\"
    package=\"com.example.{app_name}\">
    <uses-permission android:name=\"android.permission.INTERNET\"/>
    <application
        android:allowBackup=\"true\"
        android:icon=\"@mipmap/ic_launcher\"
        android:label=\"@string/app_name\"
        android:roundIcon=\"@mipmap/ic_launcher_round\"
        android:supportsRtl=\"true\"
        android:theme=\"@style/AppTheme\">
        <activity
            android:configChanges=\"orientation|keyboardHidden|screenSize\"
            android:name=\"org.kivy.android.PythonActivity\"
            android:label=\"@string/app_name\">
            <intent-filter>
                <action android:name=\"android.intent.action.MAIN\" />
                <category android:name=\"android.intent.category.LAUNCHER\" />
            </intent-filter>
        </activity>
    </application>
</manifest>""".format(app_name=app_name.lower()))

    with open(os.path.join(java_dir, 'MainActivity.java'), 'w') as f:
        f.write("""package com.example.{app_name};

import android.os.Bundle;
import org.kivy.android.PythonActivity;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;

public class MainActivity extends PythonActivity {{
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        WebView webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);
    }}
}}""".format(app_name=app_name.lower()))

    with open(os.path.join(res_dir, 'values', 'styles.xml'), 'w') as f:
        f.write("""<resources>
    <style name=\"AppTheme\" parent=\"Theme.AppCompat.Light.NoActionBar\" />
</resources>""")

    with open(os.path.join(assets_dir, 'script.py'), 'w') as f:
        f.write(python_entry_point)

    shutil.copy(os.path.join(assets_dir, 'script.py'), os.path.join(temp_dir, 'main.py'))

    print("[*] Skipping Kivy Garden and webview install. Not needed.")

    required_env_vars = ["ANDROIDSDK", "ANDROIDNDK", "ANDROIDAPI", "NDKAPI"]
    missing = [var for var in required_env_vars if var not in os.environ]
    if missing:
        print("[ERROR] Missing required environment variables:", ", ".join(missing))
        print("Please set them before running this script.")
        sys.exit(1)

    command = f"""
    p4a apk --private {temp_dir} \
    --package com.example.{app_name.lower()} \
    --name {app_name} \
    --version 1.0 \
    --bootstrap webview \
    --requirements python3 \
    --arch armeabi-v7a \
    --arch arm64-v8a \
    --debug
    """

    result = subprocess.run(
        command,
        cwd=temp_dir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print("[ERROR] p4a build failed!")
        print("Standard Output:")
        print(result.stdout)
        print("Standard Error:")
        print(result.stderr)
        shutil.rmtree(temp_dir)
        sys.exit(1)
    else:
        print("[*] APK build complete!")
        print("Standard Output:")
        print(result.stdout)

    apk_name = f"{app_name}-1.0-debug.apk"
    apk_path = os.path.join(temp_dir, 'dist', apk_name)
    if os.path.exists(apk_path):
        print(f"[*] APK found at: {apk_path}")
    else:
        apk_path = os.path.join(temp_dir, apk_name)
        if os.path.exists(apk_path):
            print(f"[*] APK found at: {apk_path}")
        else:
            print(f"[ERROR] APK not found at expected location: {apk_path}")
            print("Please check the p4a output for the actual location.")
            shutil.rmtree(temp_dir)
            sys.exit(1)

    shutil.rmtree(temp_dir)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python calc.py <app_name>")
        sys.exit(1)

    app_name = sys.argv[1]
    html_file = 'index.html'
    python_entry_point = """from jnius import autoclass

WebView = autoclass("android.webkit.WebView")
PythonActivity = autoclass("org.kivy.android.PythonActivity")

def main():
    activity = PythonActivity.mActivity
    webView = WebView(activity)
    activity.setContentView(webView)
    webView.loadUrl("file:///android_asset/index.html")

if __name__ == '__main__':
    main()
"""
    create_android_app(app_name, html_file, python_entry_point)