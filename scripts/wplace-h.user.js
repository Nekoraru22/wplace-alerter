// ==UserScript==
// @name        Wplace Alerter & Fixer
// @namespace   Violentmonkey Scripts
// @match       https://wplace.live/*
// @grant       none
// @version     2.0
// @author      Nekoraru22
// @description Intercepts a canvas method to trigger the debugger inside the target class's scope.
// @run-at      document-start
// ==/UserScript==

(function() {
    'use strict';

    // Hook Map.prototype.set
    const originalMapSet = Map.prototype.set;
    window.o = null;

    Map.prototype.set = function(key, value) {
        try {
            if (key.startsWith && key.startsWith('t=') && value.color !== undefined) {
                window.o = this;
                console.log('😺 Pixel Map Hooked');
                Map.prototype.set = originalMapSet;
            }
        } catch { }
        return originalMapSet.call(this, key, value);
    };

    // Hook Map.prototype.get
    const originalMapGet = Map.prototype.get;
    window.data = window.data || {};

    Map.prototype.get = function(key) {
        const value = originalMapGet.call(this, key);

        try {
            if (value && value.reactions && Array.isArray(value.reactions)) {
                for (const reaction of value.reactions) {
                    if (reaction && reaction.ctx?.s) {
                        const s = reaction.ctx.s;
                        if (s.crosshair && s.map && !window.data.ctx) {
                            console.log('🌍 Map functions hooked');
                            window.data.ctx = s;
                            break;
                        }
                    }
                }
            }
        } catch {}

        return value;
    };

    // Hook WeakMap.prototype.set
    const originalWeakMapSet = WeakMap.prototype.set;

    WeakMap.prototype.set = function(key, value) {
        if (key && typeof key === 'object') {
            try {
                // User class
                const hasChannel = key.channel instanceof BroadcastChannel;
                const hasRefresh = typeof key.refresh === 'function';
                if ((hasChannel || hasRefresh) && !window.data.user) {
                    console.log('🎯 User Hooked');
                    window.data.user = key;
                }
            } catch {}
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
            button.__click();

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