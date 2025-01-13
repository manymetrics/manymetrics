class ManyMetrics {
    constructor(instance, apiKey) {
        this.instance = instance;
        this.apiKey = apiKey;
        this.userId = null;
        this.sessionId = null;
    }

    init() {
        const userId = this.getCookie('userId');
        if (userId) {
            this.userId = userId;
        } else {
            this.userId = this.generateId();
            this.setCookie('userId', this.userId);
        }

        const sessionId = this.getCookie('sessionId');
        if (sessionId) {
            this.sessionId = sessionId;
        } else {
            this.sessionId = this.generateId();
            this.setCookie('sessionId', this.sessionId);
        }

        this.trackPageViews();
        this.trackFormInteractions();
    }

    track(eventType, properties = {}) {
        const reservedKeys = ['event_type', 'properties', 'user_id', 'session_id', 'path', 'client_event_time'];
        for (const key in properties) {
            if (reservedKeys.includes(key)) {
                throw new Error(`Reserved property key: ${key}`);
            }
        }

        // it isn't easy to handle property types, using strings for now
        const strProperties = {};
        for (const key in properties) {
            strProperties[key] = properties[key].toString();
        }

        const event = {
            event_type: eventType,
            user_id: this.userId,
            user_agent: navigator.userAgent,
            ...this.commonPayloadProperties(),
            ...strProperties
        };
        this.sendEvent(event);
    }

    sendEvent(event) {
        console.log('Sending event:', event);

        fetch(`${this.instance}/track`, {
            method: 'POST',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(event)
        })
            .then(response => {
                if (response.ok) {
                    console.log('Event sent successfully!');
                } else {
                    console.error('Error sending event:', response.statusText);
                }
            })
            .catch(error => {
                console.error('Error sending event:', error);
            });
    }

    getCookie(name) {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                return cookie.substring(name.length + 1);
            }
        }
        return null;
    }

    setCookie(name, value) {
        document.cookie = `${name}=${value}; path=/`;
    }

    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }

    trackPageViews() {
        const self = this;
        function trackPage() {
            self.track('Pageview', { referrer: document.referrer });
        }

        trackPage();

        window.addEventListener('popstate', function () {
            trackPage();
        });
        window.addEventListener('hashchange', function () {
            trackPage();
        });
    }

    trackFormInteractions() {
        const self = this;
        document.addEventListener('DOMContentLoaded', function () {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function (event) {
                    self.track('Form Submitted'); //, { formId: form.id, formData: self.getFormData(form) });
                });
                form.addEventListener('focus', function (event) {
                    self.track('Form Field Focused'); // { formId: form.id, fieldName: event.target.name });
                });
                form.addEventListener('blur', function (event) {
                    self.track('Form Field Blurred'); //, { formId: form.id, fieldName: event.target.name });
                });
            });
        });
    }

    identify(newUserId, traits = {}) {
        const prevUserId = this.userId;
        this.userId = newUserId;
        this.setCookie('userId', this.userId);

        const payload = {
            prev_user_id: prevUserId,
            new_user_id: this.userId,
            ...this.commonPayloadProperties(),
        };

        fetch(`${this.instance}/identify`, {
            method: 'POST',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
            .then(response => {
                if (response.ok) {
                    console.log('Identified successfully!');
                } else {
                    console.error('Error identifying:', response.statusText);
                }
            })
            .catch(error => {
                console.error('Error identifying:', error);
            });
    }

    commonPayloadProperties() {
        return {
            session_id: this.sessionId,
            client_event_time: new Date().toISOString(),
            path: window.location.pathname,
            host: window.location.host,
        };
    }

    resetIdentity() {
    // TODO
    }
}
