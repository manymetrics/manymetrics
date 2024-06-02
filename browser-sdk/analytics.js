class ManyMetrics {
    constructor(instance, apiKey, options = {}) {
        this.instance = instance;
        this.apiKey = apiKey;
        this.options = options;
        this.userId = null;
        this.sessionId = null;
        this.identified = false;
        this.queue = [];
        this.formElements = [];
    }

    identify(userId, traits = {}) {
        //     this.userId = userId;
        //     this.identified = true;
        //     this.track('identify', traits);
    }

    track(eventType, properties = {}) {
        const event = {
            eventType: eventType,
            properties,
            userId: this.userId,
            sessionId: this.sessionId,
            path: window.location.pathname,
            timestamp: new Date().getTime()
        };
        this.queue.push(event);
        this.flush();
    }

    page(properties = {}) {
        this.track('Pageview', properties);
    }

    // alias(newId, originalId) {
    //     this.track('alias', { newId, originalId });
    // }

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
        this.page({ referrer: document });

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
                self.formElements.push(form);
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
