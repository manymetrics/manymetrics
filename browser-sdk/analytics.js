class ManyMetrics {
    constructor(instance, apiKey) {
        this.instance = instance;
        this.apiKey = apiKey;
        this.userId = null;
        this.sessionId = null;
        this.identified = false;
    }

    identify(userId, traits = {}) {
        //     this.userId = userId;
        //     this.identified = true;
        //     this.track('identify', traits);
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
            session_id: this.sessionId,
            path: window.location.pathname,
            client_event_time: new Date().toISOString(),
            host: window.location.host,
            ...strProperties
        };
        this.sendEvent(event);
    }

    page(properties = {}) {
        this.track('Pageview', properties);
    }

    // alias(newId, originalId) {
    //     this.track('alias', { newId, originalId });
    // }

    sendEvent(event) {
        console.log('Sending event:', event);

        fetch(`https://${this.instance}/track`, {
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
        // track current page view
        this.page({ referrer: document.referrer });

        const self = this;
        window.addEventListener('popstate', function () {
            self.page({ referrer: document.referrer });
        });
        window.addEventListener('hashchange', function () {
            self.page({ referrer: document.referrer });
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

    getFormData(form) {
        const formData = {};
        const elements = form.elements;
        for (let i = 0; i < elements.length; i++) {
            const element = elements[i];
            if (element.name) {
                formData[element.name] = element.value;
            }
        }
        return formData;
    }
}
