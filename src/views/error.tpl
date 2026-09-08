<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} | Recoll Search</title>
    <link rel="icon" href="/logo">
    <link rel="icon" type="image/svg+xml" href="/static/logo.svg">
    <link rel="stylesheet" type="text/css" href="/static/style.css">
    <style>
        body {
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 1rem;
            position: relative;
        }

        .error-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 3rem 2.5rem;
            width: 100%;
            max-width: 500px;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            box-shadow: 0 12px 40px var(--shadow-color);
            z-index: 1;
            text-align: center;
            transition: border-color 0.3s;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .error-card:hover {
            border-color: rgba(139, 92, 246, 0.3);
        }

        .error-icon-container {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 72px;
            height: 72px;
            border-radius: 50%;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.25);
            color: #ef4444;
            margin-bottom: 1.5rem;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        }

        .error-icon-container.warning {
            background: rgba(245, 158, 11, 0.1);
            border-color: rgba(245, 158, 11, 0.25);
            color: #f59e0b;
        }

        .error-brand {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 2rem;
            padding: 6px 14px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--card-border);
            border-radius: 9999px;
            text-decoration: none;
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            transition: all 0.25s ease;
        }

        .error-brand:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: var(--card-hover-border);
            color: var(--text-primary);
            box-shadow: 0 4px 14px var(--glow-color);
            transform: translateY(-1px);
        }

        .error-logo {
            height: 24px;
            width: auto;
            max-width: 80px;
            object-fit: contain;
            filter: drop-shadow(0 2px 8px rgba(139, 92, 246, 0.4));
        }

        .error-code {
            font-size: 3.5rem;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
            background: linear-gradient(135deg, #f472b6 0%, #a855f7 45%, #38bdf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .error-title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            color: var(--text-primary);
        }

        .error-desc {
            color: var(--text-secondary);
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 1.5rem;
        }

        .error-details {
            background: rgba(15, 19, 34, 0.8);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin-bottom: 1.5rem;
            font-family: monospace;
            font-size: 0.8rem;
            color: #fca5a5;
            text-align: left;
            overflow-x: auto;
            max-height: 150px;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .back-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: var(--accent);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 0.85rem 1.75rem;
            font-size: 0.95rem;
            font-weight: 700;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 12px var(--glow-color);
        }

        .back-btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: 0 6px 16px var(--glow-color);
            color: #ffffff;
        }

        .back-btn svg {
            transition: transform 0.2s ease;
            width: 16px;
            height: 16px;
        }

        .back-btn:hover svg {
            transform: translateX(-2px);
        }
    </style>
</head>
<body>
    <div class="ambient-glow"></div>
    <div class="error-card">
        <a href="/" class="error-brand" title="Recoll Search">
            <img src="/logo" alt="Recoll Logo" class="error-logo" height="24">
            <span>Recoll Search</span>
        </a>

        <div class="error-icon-container {{'warning' if is_warning else ''}}">
            %if is_warning:
            <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
            %else:
            <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            %end
        </div>

        <h1 class="error-code">{{code}}</h1>
        <h2 class="error-title">{{title}}</h2>
        <p class="error-desc">{{desc}}</p>

        %if details:
        <div class="error-details">{{details}}</div>
        %end

        <a href="/" class="back-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
            </svg>
            Back to Search
        </a>
    </div>
</body>
</html>
