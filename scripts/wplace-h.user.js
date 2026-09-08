// ==UserScript==
// @name        Wplace Alerter & Fixer
// @namespace   Violentmonkey Scripts
// @match       https://wplace.live/*
// @grant       none
// @version     3.2.0
// @author      Nekoraru22
// @description Intercepts a canvas method to trigger the debugger inside the target class's scope.
// @run-at      document-start
// ==/UserScript==

(function() {
    'use strict';

    // Hook Map.prototype.set
    // Stays armed: the pixel map is recreated every time the paint panel is, so window.o would go stale.
    // Only the first map of each tick is kept, the erase map gets the same entries right after the pixel one.
    const originalMapSet = Map.prototype.set;
    window.o = null;
    let captureLocked = false;

    Map.prototype.set = function(key, value) {
        try {
            if (typeof key === 'string' && key.startsWith('t=') && value.color !== undefined && !captureLocked) {
                captureLocked = true;
                queueMicrotask(() => captureLocked = false);
                if (window.o !== this) {
                    window.o = this;
                    console.log('😺 Pixel Map Hooked');
                }
            }
        } catch { }
        return originalMapSet.call(this, key, value);
    };

    // Hook Map.prototype.get
    const originalMapGet = Map.prototype.get;
    window.data = window.data || {};
    const safeKeys = (o) => { try { return Object.keys(o); } catch { return []; } };

    Map.prototype.get = function(key) {
        const value = originalMapGet.call(this, key);

        try {
            if (!window.data.ctx && value && Array.isArray(value.reactions)) {
                for (const reaction of value.reactions) {
                    let ctx = reaction?.ctx;
                    let depth = 0;

                    while (ctx && depth++ < 10) {
                        const s = ctx.s;

                        if (s) {
                            const keys = safeKeys(s);
                            if (keys.includes('map') && keys.includes('zoom')) {
                                console.log('🌍 Map functions hooked');
                                window.data.ctx = s;
                                break;
                            }
                        }
                        ctx = ctx.p;
                    }
                    if (window.data.ctx) break;
                }
            }
        } catch {}
        return value;
    };

    // Unhook Map.prototype.get after finding the context
    const unhookTimer = setInterval(() => {
        if (window.data.ctx) {
            Map.prototype.get = originalMapGet;
            clearInterval(unhookTimer);
            console.log('🔌 Map.get unhooked');
        }
    }, 500);

    setTimeout(() => {
        clearInterval(unhookTimer);
        if (Map.prototype.get !== originalMapGet) {
            Map.prototype.get = originalMapGet;
            console.warn('⚠️ Map ctx not found, unhooking Map.get');
        }
    }, 30000);

    // Lazy access to the MapLibre instance
    window.getMap = () => {
        const m = window.data.ctx?.map;
        return (m && typeof m === 'object' && 'v' in m && 'reactions' in m) ? m.v : m;
    };

    // Hook WeakMap.prototype.set
    const originalWeakMapSet = WeakMap.prototype.set;

    // User class: only the user store owns both 'data' and 'charges' (other stores also have refresh())
    const isUserStore = (key) => {
        try {
            if (!key || typeof key !== 'object') return false;
            if (!('data' in key) || !('charges' in key)) return false;
            return key.channel instanceof BroadcastChannel || typeof key.refresh === 'function';
        } catch {
            return false;
        }
    };

    WeakMap.prototype.set = function(key, value) {
        if (!window.data.user && isUserStore(key)) {
            console.log('🎯 User Hooked');
            window.data.user = key;
            WeakMap.prototype.set = originalWeakMapSet;
        }
        return originalWeakMapSet.call(this, key, value);
    };

    // Canvas interaction logic
    const captures = [];
    window.__examineCaptures = () => captures;

    let inter = setInterval(() => {
        // Look for the canvas element
        const canvas = document.querySelector('.maplibregl-interactive');
        if (!canvas) {
            return;
        }

        setTimeout(() => {
            // Click at top-left corner of the canvas
            const rect = canvas.getBoundingClientRect();
            const createClickEvent = () => new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: rect.left,
                clientY: rect.top,
                screenX: rect.left,
                screenY: rect.top,
                offsetX: 0,
                offsetY: 0,
                pageX: rect.left + window.pageXOffset,
                pageY: rect.top + window.pageYOffset,
                button: 0,
                buttons: 1,
                detail: 1
            });

            // Check if the paint button exists and click it
            const button = document.querySelector('button.btn-lg.relative');
            if (!button) {
                console.error('Button not found.');
                return;
            }
            button.click();

            setTimeout(() => {
                // Click on the canvas to place a pixel
                canvas.dispatchEvent(createClickEvent());

                setTimeout(() => {
                    // Press erase button and erase the pixel
                    const tooltipButton = document.querySelector("div.tooltip.ml-auto")?.querySelector("button");
                    if (tooltipButton) {
                        tooltipButton.click();

                        setTimeout(() => {
                            canvas.dispatchEvent(createClickEvent());
                        }, 200);
                    }
                }, 300);
            }, 500);
        }, 1000);

        clearInterval(inter);
    }, 100);
})();