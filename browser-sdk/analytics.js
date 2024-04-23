class ManyMetrics {
    constructor(instance, apiKey, options = {}) {
        this.instance = instance;
        this.apiKey = apiKey;
        this.options = options;
        this.userId = null;
        this.sessionId = null;
        this.trackingId = null;
        this.identified = false;
        this.queue = [];
        this.formElements = [];
    }

    identify(userId, traits = {}) {
        this.userId = userId;
        this.identified = true;
        this.track('identify', traits);
    }

    track(eventName, properties = {}) {
        const event = {
            event: eventName,
            properties,
            userId: this.userId,
            sessionId: this.sessionId,
            trackingId: this.trackingId,
            timestamp: new Date().getTime()
        };
        this.queue.push(event);
        this.flush();
    }

    page(viewName, properties = {}) {
        this.track('page', { viewName, ...properties });
    }

    alias(newId, originalId) {
        this.track('alias', { newId, originalId });
    }

    flush() {
        if (this.queue.length > 0) {
            const events = this.queue.splice(0, this.queue.length);
            this.sendEvents(events);
        }
    }

    sendEvents(events) {
        fetch(`https://${this.instance}/prod/e`, {
            method: 'POST',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(events)
        })
            .then(response => {
                if (response.ok) {
                    console.log('Events sent successfully!');
                } else {
                    console.error('Error sending events:', response.statusText);
                }
            })
            .catch(error => {
                console.error('Error sending events:', error);
            });
    }

    init() {
        this.sessionId = this.generateSessionId();
        this.trackingId = this.generateTrackingId();
        this.flushInterval = setInterval(this.flush.bind(this), 1000);

        this.trackPageViews();
        this.trackFormInteractions();
    }

    generateSessionId() {
        return Math.random().toString(36).substr(2, 9);
    }

    generateTrackingId() {
        return Math.random().toString(36).substr(2, 12);
    }

    trackPageViews() {
        const self = this;
        window.addEventListener('popstate', function () {
            self.page(window.location.pathname, { referrer: document.referrer });
        });
        window.addEventListener('hashchange', function () {
            self.page(window.location.pathname, { referrer: document.referrer });
        });
    }

    trackFormInteractions() {
        const self = this;
        document.addEventListener('DOMContentLoaded', function () {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                self.formElements.push(form);
                form.addEventListener('submit', function (event) {
                    self.track('Form Submitted', { formId: form.id, formData: self.getFormData(form) });
                });
                form.addEventListener('focus', function (event) {
                    self.track('Form Field Focused', { formId: form.id, fieldName: event.target.name });
                });
                form.addEventListener('blur', function (event) {
                    self.track('Form Field Blurred', { formId: form.id, fieldName: event.target.name });
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
