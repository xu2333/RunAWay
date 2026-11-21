package io.runaway.taste;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.provider.DocumentsContract;
import android.util.Base64;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.OutputStream;

/** Saves only to the document URI explicitly selected by the owner. No storage permissions. */
@CapacitorPlugin(name = "SaveDocument")
public class SaveDocumentPlugin extends Plugin {
    @PluginMethod
    public void save(PluginCall call) {
        String name = call.getString("name", "");
        String mime = call.getString("mime", "");
        String data = call.getString("data", "");
        if (!name.matches("[A-Za-z0-9_.-]{1,120}") || data.length() > 2800000 ||
            !(mime.equals("application/json") || mime.equals("application/zip") || mime.equals("text/plain"))) {
            call.reject("无效的导出文件。");
            return;
        }
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType(mime);
        intent.putExtra(Intent.EXTRA_TITLE, name);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            intent.putExtra(DocumentsContract.EXTRA_INITIAL_URI,
                Uri.parse("content://com.android.providers.downloads.documents/root/downloads"));
        }
        startActivityForResult(call, intent, "saveResult");
    }

    @ActivityCallback
    private void saveResult(PluginCall call, ActivityResult result) {
        if (call == null) return; // The process may have been reclaimed by Android.
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null) {
            call.reject("已取消保存。");
            return;
        }
        Uri uri = result.getData().getData();
        if (uri == null || !"content".equals(uri.getScheme())) {
            call.reject("没有取得系统选择的文件位置。");
            return;
        }
        // Do file I/O away from the UI thread; the call remains alive until resolve/reject.
        getBridge().execute(() -> {
            try {
                byte[] bytes = Base64.decode(call.getString("data", ""), Base64.NO_WRAP);
                try (OutputStream stream = getContext().getContentResolver().openOutputStream(uri, "wt")) {
                    if (stream == null) throw new IllegalStateException("No output stream");
                    stream.write(bytes);
                    stream.flush();
                }
                JSObject value = new JSObject();
                value.put("status", "saved");
                call.resolve(value);
            } catch (Exception error) {
                // Do not return file paths, content or provider-specific diagnostics.
                call.reject("文件未能完整保存。请检查所选位置后重新导出。");
            }
        });
    }

    @PluginMethod
    public void clear(PluginCall call) {
        // Android keeps the export bytes in the pending call, not in an app file.
        call.resolve();
    }
}
