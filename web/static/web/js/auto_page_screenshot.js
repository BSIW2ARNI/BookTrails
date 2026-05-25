(function () {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return '';
    }

    async function sendScreenshot() {
        if (typeof window.html2canvas !== 'function') {
            return;
        }

        const key = `auto_screenshot_sent:${window.location.pathname}${window.location.search}`;
        if (window.sessionStorage.getItem(key)) {
            return;
        }

        await new Promise((resolve) => window.setTimeout(resolve, 800));

        const canvas = await window.html2canvas(document.body, {
            backgroundColor: '#ffffff',
            scale: 1.5,
            useCORS: true,
            scrollX: 0,
            scrollY: -window.scrollY,
            windowWidth: document.documentElement.scrollWidth,
            windowHeight: document.documentElement.scrollHeight,
        });

        const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/png'));
        if (!blob) {
            return;
        }

        const formData = new FormData();
        formData.append('image', blob, 'page-screenshot.png');
        formData.append('url_path', `${window.location.pathname}${window.location.search}${window.location.hash}`);

        const response = await fetch('/system/save-page-screenshot/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: formData,
        });

        if (!response.ok) {
            return;
        }

        const payload = await response.json();
        if (payload && payload.ok) {
            window.sessionStorage.setItem(key, '1');
        }
    }

    window.addEventListener('pageshow', function () {
        sendScreenshot().catch(function (error) {
            console.error('auto_page_screenshot failed', error);
        });
    });
}());
