package io.runaway.taste;

import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.uiautomator.By;
import androidx.test.uiautomator.UiDevice;
import androidx.test.uiautomator.UiObject2;
import androidx.test.uiautomator.Until;
import org.json.JSONObject;
import org.json.JSONTokener;
import java.util.regex.Pattern;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

/** Runs the real bundled app in Android WebView, without network or a model. */
@RunWith(AndroidJUnit4.class)
public class LocalRuntimeTest {
    private String js(ActivityScenario<MainActivity> scenario, String script) throws Exception {
        AtomicReference<String> value = new AtomicReference<>();
        CountDownLatch complete = new CountDownLatch(1);
        scenario.onActivity(activity -> activity.getBridge().getWebView().evaluateJavascript(script, result -> {
            value.set(result);
            complete.countDown();
        }));
        assertTrue("WebView callback missing", complete.await(10, TimeUnit.SECONDS));
        return value.get();
    }
    private void await(ActivityScenario<MainActivity> scenario, String condition) throws Exception {
        for (int i = 0; i < 80; i++) {
            if ("true".equals(js(scenario, "Boolean(" + condition + ")"))) return;
            Thread.sleep(250);
        }
        fail("Bundled app did not reach the expected state");
    }
    private void tapElement(ActivityScenario<MainActivity> scenario, UiDevice device, String id) throws Exception {
        String encoded = js(scenario, "(() => { const e=document.getElementById(" + JSONObject.quote(id) + "); e.scrollIntoView({block:'center'}); const r=e.getBoundingClientRect(); return JSON.stringify({x:r.x+r.width/2,y:r.y+r.height/2,scale:devicePixelRatio}); })()");
        JSONObject point = new JSONObject((String) new JSONTokener(encoded).nextValue());
        int[] offset = new int[2];
        scenario.onActivity(activity -> activity.getBridge().getWebView().getLocationOnScreen(offset));
        device.click(offset[0] + (int) (point.getDouble("x") * point.getDouble("scale")),
                     offset[1] + (int) (point.getDouble("y") * point.getDouble("scale")));
    }
    @Test
    public void bundledAppCanValidateFictionalProfileAndReachNativeSaveBridge() throws Exception {
        try (ActivityScenario<MainActivity> scenario = ActivityScenario.launch(MainActivity.class)) {
            await(scenario, "document.querySelectorAll('[data-harness]').length === 3");
            assertEquals("true", js(scenario, "Boolean(window.isSecureContext && crypto.subtle && crypto.randomUUID)"));
            assertEquals("true", js(scenario, "Boolean(window.Capacitor.isNativePlatform() && typeof window.Capacitor.Plugins.SaveDocument.save === 'function')"));
            js(scenario, "document.getElementById('demo').click()");
            await(scenario, "!document.getElementById('result-panel').hidden");
            assertEquals("true", js(scenario, "document.getElementById('prompt').value.length > 100 && document.querySelectorAll('#evidence .claim').length > 0"));
            assertEquals("true", js(scenario, "document.getElementById('result-status').textContent.includes('虚构')"));
        }
    }
    @Test
    public void systemPickerCanCancelSaveAndReopenPrivateArchive() throws Exception {
        UiDevice device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation());
        try (ActivityScenario<MainActivity> scenario = ActivityScenario.launch(MainActivity.class)) {
            await(scenario, "document.querySelectorAll('[data-harness]').length === 3");
            js(scenario, "document.getElementById('demo').click()");
            await(scenario, "!document.getElementById('result-panel').hidden");
            String expected = js(scenario, "document.getElementById('prompt').value");
            js(scenario, "document.getElementById('save-private').click()");
            UiObject2 save = device.wait(Until.findObject(By.text(Pattern.compile("(?i)^save$"))), 15000);
            assertNotNull("System save picker did not appear", save);
            device.pressBack();
            await(scenario, "document.getElementById('notice').textContent.includes('已取消保存')");

            js(scenario, "document.getElementById('save-private').click()");
            save = device.wait(Until.findObject(By.text(Pattern.compile("(?i)^save$"))), 15000);
            assertNotNull("Save after cancellation did not open", save);
            save.click();
            await(scenario, "document.getElementById('notice').textContent.includes('系统已完成文件保存')");

            // JS confirm blocks evaluateJavascript's result callback. Tap as a
            // real user so the test can respond to the native dialog next.
            tapElement(scenario, device, "clear");
            UiObject2 confirm = device.wait(Until.findObject(By.res("android", "button1")), 5000);
            assertNotNull("Clear confirmation did not open", confirm);
            confirm.click();
            await(scenario, "!document.getElementById('source-panel').hidden && document.getElementById('source').value === ''");
            tapElement(scenario, device, "archive-file");
            UiObject2 archive = device.wait(Until.findObject(By.text("runaway.private.json")), 8000);
            if (archive == null) {
                UiObject2 roots = device.findObject(By.desc("Show roots"));
                if (roots != null) roots.click();
                UiObject2 downloads = device.wait(Until.findObject(By.text("Downloads")), 5000);
                if (downloads != null) downloads.click();
                archive = device.wait(Until.findObject(By.text("runaway.private.json")), 8000);
            }
            assertNotNull("Saved archive was not visible to the system open picker", archive);
            archive.click();
            await(scenario, "!document.getElementById('result-panel').hidden");
            assertEquals(expected, js(scenario, "document.getElementById('prompt').value"));
            assertEquals("true", js(scenario, "document.getElementById('result-status').textContent.includes('虚构')"));
        } finally {
            // Only fictional demo content exists on this fresh CI emulator.
            java.io.File window = new java.io.File(InstrumentationRegistry.getInstrumentation()
                .getTargetContext().getExternalFilesDir(null), "native-picker-window.xml");
            device.dumpWindowHierarchy(window);
            // UTP can uninstall the app before the host pulls external files.
            // Retain the same fictional-only diagnostic in the captured logcat.
            try (java.io.FileReader reader = new java.io.FileReader(window)) {
                char[] chunk = new char[1500];
                int count;
                while ((count = reader.read(chunk)) != -1) {
                    System.out.println("RUNAWAY_NATIVE_WINDOW " + new String(chunk, 0, count));
                }
            }
        }
    }
}
