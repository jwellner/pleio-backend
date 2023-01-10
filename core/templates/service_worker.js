// Register event listener for the 'push' event.
self.addEventListener('push', function (event) {
    // Retrieve the textual payload from event.data (a PushMessageData object).
    // Other formats are supported (ArrayBuffer, Blob, JSON), check out the documentation
    // on https://developer.mozilla.org/en-US/docs/Web/API/PushMessageData.
    var payload = event.data ? event.data.text() : { "head": "No Content", "body": "No Content", "icon": "" },
        data = JSON.parse(payload),
        head = data.head,
        body = data.body,
        icon = data.icon;

    // If no url was received, it opens the home page of the website that sent the notification
    // Whitout this, it would open undefined or the service worker file.
    var url = data.url ? `${self.location.origin}${data.url}` : self.location.origin;

    // Keep the service worker alive until the notification is created.
    event.waitUntil(
        // Show a notification with title 'ServiceWorker Cookbook' and use the payload
        // as the body.
        self.registration.showNotification(head, {
            body: body,
            icon: icon,
            data: { url: url }
        })
    );
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();

    if (event.notification.data.url) {
        var targetUrl = new URL(event.notification.data.url);

        // Attempt to fetch open tabs
        event.waitUntil(self.clients.matchAll({ type: 'window' }).then(function (clientList) {
            // No match by default
            var matchFound = false;

            // Traverse clients list
            for (var client of clientList) {
                // Parse url
                var clientUrl = new URL(client.url);

                // Check host matches
                if (clientUrl.host === targetUrl.host && 'focus' in client) {
                    // Update URL
                    client.navigate(url);

                    // Focus existing window
                    client.focus();

                    // Avoid opening a new window
                    noMatch = true;
                }
            }

            // If no open tabs, or none match the host, open a new window
            if (!matchFound) {
                event.waitUntil(self.clients.openWindow(url));
            }
        }));
    }

})