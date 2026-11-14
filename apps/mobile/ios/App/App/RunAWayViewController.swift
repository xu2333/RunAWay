import Capacitor

class RunAWayViewController: CAPBridgeViewController {
    override func capacitorDidLoad() {
        bridge?.registerPluginInstance(SaveDocumentPlugin())
    }
}
