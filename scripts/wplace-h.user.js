// ==UserScript==
// @name        Wplace Alerter & Fixer
// @namespace   Violentmonkey Scripts
// @match       https://wplace.live/*
// @grant       none
// @version     1.7
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
                console.log('Pixels Map Hooked');
                Map.prototype.set = originalMapSet;
            }
        } catch { }
        return originalMapSet.call(this, key, value);
    };

    // Hook WeakMap.prototype.set
    const originalWeakMapSet = WeakMap.prototype.set;
    window.data = {};

    WeakMap.prototype.set = function(key, value) {
        try {
            if (key?.current?.entries?.().next?.().value?.[0].reactions?.length > 0) {
                for (const i in key.current.entries().next().value[0].reactions) {
                    const x = key.current.entries().next().value[0].reactions[i];
                    const o = x?.ctx?.s;
                    if (o !== undefined && o.value === undefined) {
                        if (o.user) {
                            window.data.user = o;
                            console.log('User function Hooked');
                        } else if (o.crosshair) {
                            window.data.ctx = o;
                            console.log('Ctx function Hooked');
                        }
                    }
                }
            }
        } catch { }
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