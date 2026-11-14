package io.runaway.taste;

import com.getcapacitor.BridgeActivity;
import android.os.Bundle;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(SaveDocumentPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
