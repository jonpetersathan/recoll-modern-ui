        <footer class="app-footer">
            <div class="footer-info">
                <span>Recoll Modern UI</span>
                <span id="footer-index-badge" class="security-badge status-ready" title="Search Index Status">Index Ready</span>
                <span>&bull;</span>
                <span>Powered by Recoll &amp; Bottle</span>
            </div>
        </footer>
    </div>

    <!-- Themed Application Confirmation / Alert Modal Dialog -->
    <div id="app-dialog-overlay" class="modal-backdrop" style="display: none;">
        <div class="modal-dialog confirm-modal-dialog" role="dialog" aria-modal="true">
            <div class="modal-header">
                <div class="modal-title-wrap">
                    <span id="app-dialog-icon" class="dialog-icon-wrap"></span>
                    <h3 id="app-dialog-title">Confirm Action</h3>
                </div>
                <button type="button" class="modal-close-btn" id="btn-close-app-dialog" title="Close dialog">&times;</button>
            </div>
            <div class="modal-body">
                <p id="app-dialog-message" class="confirm-modal-message"></p>
            </div>
            <div class="modal-footer" id="app-dialog-footer">
                <button type="button" class="btn btn-secondary" id="btn-cancel-app-dialog">Cancel</button>
                <button type="button" class="btn btn-danger" id="btn-confirm-app-dialog">Confirm</button>
                <button type="button" class="btn btn-primary" id="btn-save-app-dialog" style="display: none;">Save &amp; Leave</button>
            </div>
        </div>
    </div>
</body>
</html>
