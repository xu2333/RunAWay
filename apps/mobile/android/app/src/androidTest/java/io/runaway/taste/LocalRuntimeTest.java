package io.runaway.taste;

import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
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
}
