<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Recoll Search{{title}}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="/static/style.css?v=0.9.5">
    <script type="text/javascript" src="/static/extra.js?v=0.9.5" defer></script>
    <link rel="icon" href="/logo">
    <link rel="icon" type="image/svg+xml" href="/static/logo.svg">
    <link rel="icon" type="image/png" href="/static/recoll.png">
    <link rel="search" type="application/opensearchdescription+xml" title="recoll" href="/osd.xml">
</head>
<body>
    <div class="ambient-glow"></div>
    <div id="fade" class="search-loading-overlay">
        <div class="search-loader-container">
            <div class="search-gyro-spinner">
                <div class="gyro-ring gyro-ring-outer"></div>
                <div class="gyro-ring gyro-ring-middle"></div>
                <div class="gyro-ring gyro-ring-inner"></div>
                <div class="gyro-core-pulse"></div>
            </div>
            <div class="search-loading-status">
                <span class="search-loading-text">Searching Index</span>
                <span class="search-loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                </span>
            </div>
            <div class="search-loading-subtext">Executing Query on Recoll Engine</div>
        </div>
    </div>
    <div class="container">
        <header class="app-header">
            <div class="header-brand">
                <a href="./" class="header-logo-link" title="Recoll Home">
                    <img src="/logo" alt="Recoll Logo" class="header-logo" height="48">
                </a>
                <div class="header-title">
                    <h1><a href="./">Recoll Search</a></h1>
                    <p>Blazing Fast File Index And Query Solution</p>
                </div>
            </div>
            <div class="header-actions">
                % page_title = title if defined('title') else ''
                % active_tab = get('active_tab', '')
                <a href="./" class="btn btn-secondary nav-action-btn{{ ' active' if active_tab == 'search' or (page_title == '' and not active_tab) or (page_title and page_title.startswith(':')) else '' }}" title="New Search">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                        <polyline points="9 22 9 12 15 12 15 22"></polyline>
                    </svg>
                    <span>Search</span>
                </a>
                <a href="browser" class="btn btn-secondary nav-action-btn{{ ' active' if active_tab == 'browser' or 'Browser' in page_title else '' }}" title="File &amp; Folder Browser">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <span>Browser</span>
                </a>
                % is_admin_val = get('is_admin', None)
                % if is_admin_val is None:
                %     is_admin_val = config.get('is_admin', None) if (defined('config') and config) else None
                % end
                % if is_admin_val is None:
                %     try:
                %         from recollweb.auth import get_current_user, is_admin_user
                %         _u = get('current_user', None) or (config.get('current_user', None) if (defined('config') and config) else None) or get_current_user()
                %         is_admin_val = is_admin_user(_u)
                %     except Exception:
                %         is_admin_val = True
                %     end
                % end
                % if is_admin_val:
                <a href="index-manager" class="btn btn-secondary nav-action-btn{{ ' active' if active_tab == 'index' or 'Index' in page_title else '' }}" title="Index &amp; Metadata Rules">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <ellipse cx="12" cy="5" rx="9" ry="3"></ellipse>
                        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path>
                        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>
                    </svg>
                    <span>Index</span>
                </a>
                % end
                <a href="settings" class="btn btn-secondary nav-action-btn{{ ' active' if active_tab == 'settings' or 'Settings' in page_title else '' }}" title="Preferences">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3"></circle>
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                    </svg>
                    <span>Settings</span>
                </a>
                % cur_user = get('current_user', None)
                % if cur_user is None:
                %     cur_user = config.get('current_user', None) if (defined('config') and config) else None
                % end
                % if cur_user is None:
                %     try:
                %         from recollweb.auth import get_current_user
                %         cur_user = get_current_user() or 'default'
                %     except Exception:
                %         cur_user = 'default'
                %     end
                % end
                % cur_role = get('user_role', '') if (defined('user_role') and user_role) else ('admin' if is_admin_val else 'user')
                <div class="user-profile-badge" title="User: {{cur_user}} ({{cur_role.capitalize()}})">
                    <span class="user-avatar-icon">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                    </span>
                    <span class="user-name">{{cur_user}}</span>
                    <span class="badge-pill user-role-pill {{ 'badge-admin' if cur_role == 'admin' else 'badge-user' }}">{{cur_role}}</span>
                </div>
            </div>

        </header>
