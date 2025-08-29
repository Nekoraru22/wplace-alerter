// ==UserScript==
// @name        Wplace DK Class Hunter (Debugger Poisoning)
// @namespace   Violentmonkey Scripts
// @match       https://wplace.live/*
// @grant       none
// @version     1.6
// @author      -
// @description Intercepts a canvas method to trigger the debugger inside the target class's scope.
// @run-at      document-start
// ==/UserScript==

(function() {
    'use strict';
    const originalMapSet = Map.prototype.set;
    const captures = [];
    window.ctx = new Set();
    Map.prototype.set = function(key, value) {
        try {
            if (key.startsWith && key.startsWith('t=') && value.color !== undefined) {
                window.o = this;
                console.log('Hooked');
                Map.prototype.set = originalMapSet
            }
        } catch { }
        return originalMapSet.call(this, key, value);
    };
    window.__examineCaptures = () => captures;
    let inter = setInterval(() => {
        const canvas = document.querySelector('.maplibregl-interactive');
        if (!canvas) {
            return;
        }
        setTimeout(() => {
            document.querySelector('button.btn-lg.relative').__click();
            setTimeout(() => {
                const rect = canvas.getBoundingClientRect();
                const clickEvent = new MouseEvent('click', {
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
                canvas.dispatchEvent(clickEvent);
                const clickEvent2 = new MouseEvent('click', {
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
                canvas.dispatchEvent(clickEvent2);

                setTimeout(() => {
                    const tooltipButton = document.querySelector("div.tooltip.ml-auto").querySelector("button");
                    if (tooltipButton) {
                        tooltipButton.click();

                        setTimeout(() => {
                            const clickEvent3 = new MouseEvent('click', {
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
                            canvas.dispatchEvent(clickEvent3);
                        }, 200);
                    }
                }, 300);

            }, 500);
        }, 1000);
        clearInterval(inter);
    }, 100);
})();

(function() {
    'use strict';

    const originalWeakMapSet = WeakMap.prototype.set;
    const captures = [];
    window.data = {};

    WeakMap.prototype.set = function(key, value) {
        try {
            if (key?.current?.entries?.().next?.().value?.[0].reactions?.length > 0) {
                for (const i in key.current.entries().next().value[0].reactions) {
                    const x = key.current.entries().next().value[0].reactions[i];
                    const o = x?.ctx?.s;
                    if (o !== undefined && o.value === undefined) {
                        if (o.user)
                            window.data.user = o;
                        else if (o.crosshair)
                            window.data.ctx = o;
                    }
                    // WeakMap.prototype.set = originalWeakMapSet;
                }
            }
        } catch { }
        return originalWeakMapSet.call(this, key, value);
    };

    window.__examineCaptures = () => captures;

    let inter = setInterval(() => {
        const canvas = document.querySelector('.maplibregl-interactive');
        if (!canvas) {
            return;
        }

        setTimeout(() => {
            const rect = canvas.getBoundingClientRect();
            console.log('Loaded, clicking', canvas);

            const clickEvent = new MouseEvent('click', {
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

            canvas.dispatchEvent(clickEvent);
        }, 1000);

        clearInterval(inter);
    }, 100);
})();