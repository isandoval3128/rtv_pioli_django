!function(t, e) {
    "function" == typeof define && define.amd ? define(["jquery"], e) : "undefined" != typeof exports ? e(require("jquery")) : (e(t.jquery),
    t.metisMenu = {})
}(this, function(t) {
    "use strict";
    (t = t) && t.__esModule;
    var n = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function(t) {
        return typeof t
    }
    : function(t) {
        return t && "function" == typeof Symbol && t.constructor === Symbol && t !== Symbol.prototype ? "symbol" : typeof t
    }
    ;
    var s, e, i, r, a = (s = jQuery,
    e = !1,
    i = {
        WebkitTransition: "webkitTransitionEnd",
        MozTransition: "transitionend",
        OTransition: "oTransitionEnd otransitionend",
        transition: "transitionend"
    },
    r = {
        TRANSITION_END: "mmTransitionEnd",
        triggerTransitionEnd: function(t) {
            s(t).trigger(e.end)
        },
        supportsTransitionEnd: function() {
            return Boolean(e)
        }
    },
    e = function() {
        if (window.QUnit)
            return !1;
        var t, e = document.createElement("mm");
        for (t in i)
            if (void 0 !== e.style[t])
                return {
                    end: i[t]
                };
        return !1
    }(),
    s.fn.emulateTransitionEnd = o,
    r.supportsTransitionEnd() && (s.event.special[r.TRANSITION_END] = {
        bindType: e.end,
        delegateType: e.end,
        handle: function(t) {
            if (s(t.target).is(this))
                return t.handleObj.handler.apply(this, arguments)
        }
    }),
    r);
    function o(t) {
        var e = this
          , i = !1;
        return s(this).one(r.TRANSITION_END, function() {
            i = !0
        }),
        setTimeout(function() {
            i || r.triggerTransitionEnd(e)
        }, t),
        this
    }
    var h, l, g, p, u, c, d;
    h = jQuery,
    t = "." + (g = l = "metisMenu"),
    p = h.fn[l],
    u = {
        toggle: !0,
        preventDefault: !0,
        activeClass: "active",
        collapseClass: "collapse",
        collapseInClass: "in",
        collapsingClass: "collapsing",
        triggerElement: "a",
        parentTrigger: "li",
        subMenu: "ul"
    },
    c = {
        SHOW: "show" + t,
        SHOWN: "shown" + t,
        HIDE: "hide" + t,
        HIDDEN: "hidden" + t,
        CLICK_DATA_API: "click" + t + ".data-api"
    },
    f.prototype.init = function() {
        var r = this;
        h(this._element).find(this._config.parentTrigger + "." + this._config.activeClass).has(this._config.subMenu).children(this._config.subMenu).attr("aria-expanded", !0).addClass(this._config.collapseClass + " " + this._config.collapseInClass),
        h(this._element).find(this._config.parentTrigger).not("." + this._config.activeClass).has(this._config.subMenu).children(this._config.subMenu).attr("aria-expanded", !1).addClass(this._config.collapseClass),
        h(this._element).find(this._config.parentTrigger).has(this._config.subMenu).children(this._config.triggerElement).on(c.CLICK_DATA_API, function(t) {
            var e = h(this)
              , i = e.parent(r._config.parentTrigger)
              , s = i.siblings(r._config.parentTrigger).children(r._config.triggerElement)
              , n = i.children(r._config.subMenu);
            r._config.preventDefault && t.preventDefault(),
            "true" !== e.attr("aria-disabled") && (i.hasClass(r._config.activeClass) ? (e.attr("aria-expanded", !1),
            r._hide(n)) : (r._show(n),
            e.attr("aria-expanded", !0),
            r._config.toggle && s.attr("aria-expanded", !1)),
            r._config.onTransitionStart && r._config.onTransitionStart(t))
        })
    }
    ,
    f.prototype._show = function(t) {
        var e, i;
        this._transitioning || h(t).hasClass(this._config.collapsingClass) || (e = this,
        i = h(t),
        t = h.Event(c.SHOW),
        i.trigger(t),
        t.isDefaultPrevented() || (i.parent(this._config.parentTrigger).addClass(this._config.activeClass),
        this._config.toggle && this._hide(i.parent(this._config.parentTrigger).siblings().children(this._config.subMenu + "." + this._config.collapseInClass).attr("aria-expanded", !1)),
        i.removeClass(this._config.collapseClass).addClass(this._config.collapsingClass).height(0),
        this.setTransitioning(!0),
        t = function() {
            i.removeClass(e._config.collapsingClass).addClass(e._config.collapseClass + " " + e._config.collapseInClass).height("").attr("aria-expanded", !0),
            e.setTransitioning(!1),
            i.trigger(c.SHOWN)
        }
        ,
        a.supportsTransitionEnd() ? i.height(i[0].scrollHeight).one(a.TRANSITION_END, t).emulateTransitionEnd(350) : t()))
    }
    ,
    f.prototype._hide = function(t) {
        var e, i;
        !this._transitioning && h(t).hasClass(this._config.collapseInClass) && (e = this,
        i = h(t),
        t = h.Event(c.HIDE),
        i.trigger(t),
        t.isDefaultPrevented() || (i.parent(this._config.parentTrigger).removeClass(this._config.activeClass),
        i.height(i.height())[0].offsetHeight,
        i.addClass(this._config.collapsingClass).removeClass(this._config.collapseClass).removeClass(this._config.collapseInClass),
        this.setTransitioning(!0),
        t = function() {
            e._transitioning && e._config.onTransitionEnd && e._config.onTransitionEnd(),
            e.setTransitioning(!1),
            i.trigger(c.HIDDEN),
            i.removeClass(e._config.collapsingClass).addClass(e._config.collapseClass).attr("aria-expanded", !1)
        }
        ,
        !a.supportsTransitionEnd() || 0 == i.height() || "none" == i.css("display") ? t() : i.height(0).one(a.TRANSITION_END, t).emulateTransitionEnd(350)))
    }
    ,
    f.prototype.setTransitioning = function(t) {
        this._transitioning = t
    }
    ,
    f.prototype.dispose = function() {
        h.removeData(this._element, g),
        h(this._element).find(this._config.parentTrigger).has(this._config.subMenu).children(this._config.triggerElement).off("click"),
        this._transitioning = null,
        this._config = null,
        this._element = null
    }
    ,
    f.prototype._getConfig = function(t) {
        return t = h.extend({}, u, t)
    }
    ,
    f._jQueryInterface = function(s) {
        return this.each(function() {
            var t = h(this)
              , e = t.data(g)
              , i = h.extend({}, u, t.data(), "object" === (void 0 === s ? "undefined" : n(s)) && s);
            if (!e && /dispose/.test(s) && this.dispose(),
            e || (e = new f(this,i),
            t.data(g, e)),
            "string" == typeof s) {
                if (void 0 === e[s])
                    throw new Error('No method named "' + s + '"');
                e[s]()
            }
        })
    }
    ,
    d = f,
    h.fn[l] = d._jQueryInterface,
    h.fn[l].Constructor = d,
    h.fn[l].noConflict = function() {
        return h.fn[l] = p,
        d._jQueryInterface
    }
    ;
    function f(t, e) {
        !function(t, e) {
            if (!(t instanceof e))
                throw new TypeError("Cannot call a class as a function")
        }(this, f),
        this._element = t,
        this._config = this._getConfig(e),
        this._transitioning = null,
        this.init()
    }
}),
function(n) {
    "use strict";
    function v(t, e) {
        this.$element = n(t),
        this.options = n.extend({}, v.defaults, e)
    }
    v.defaults = {
        transition_delay: 300,
        refresh_speed: 50,
        display_text: "none",
        use_percentage: !0,
        percent_format: function(t) {
            return t + "%"
        },
        amount_format: function(t, e) {
            return t + " / " + e
        },
        update: n.noop,
        done: n.noop,
        fail: n.noop
    },
    v.prototype.transition = function() {
        var r, t, a = this.$element, o = a.parent(), h = this.$back_text, l = this.$front_text, g = this.options, p = parseInt(a.attr("data-transitiongoal")), u = parseInt(a.attr("aria-valuemin")) || 0, c = parseInt(a.attr("aria-valuemax")) || 100, d = o.hasClass("vertical"), f = (g.update && "function" == typeof g.update ? g : v.defaults).update, m = (g.done && "function" == typeof g.done ? g : v.defaults).done, e = (g.fail && "function" == typeof g.fail ? g : v.defaults).fail;
        isNaN(p) ? e("data-transitiongoal not set") : (r = Math.round(100 * (p - u) / (c - u)),
        "center" !== g.display_text || h || l || (this.$back_text = h = n("<span>").addClass("progressbar-back-text").prependTo(o),
        this.$front_text = l = n("<span>").addClass("progressbar-front-text").prependTo(a),
        d ? (t = o.css("height"),
        h.css({
            height: t,
            "line-height": t
        }),
        l.css({
            height: t,
            "line-height": t
        }),
        n(window).resize(function() {
            t = o.css("height"),
            h.css({
                height: t,
                "line-height": t
            }),
            l.css({
                height: t,
                "line-height": t
            })
        })) : (t = o.css("width"),
        l.css({
            width: t
        }),
        n(window).resize(function() {
            t = o.css("width"),
            l.css({
                width: t
            })
        }))),
        setTimeout(function() {
            var t, e, i, s;
            d ? a.css("height", r + "%") : a.css("width", r + "%");
            var n = setInterval(function() {
                s = d ? (i = a.height(),
                o.height()) : (i = a.width(),
                o.width()),
                t = Math.round(100 * i / s),
                e = Math.round(u + i / s * (c - u)),
                r <= t && (t = r,
                e = p,
                m(a),
                clearInterval(n)),
                "none" !== g.display_text && (s = g.use_percentage ? g.percent_format(t) : g.amount_format(e, c, u),
                "fill" === g.display_text ? a.text(s) : "center" === g.display_text && (h.text(s),
                l.text(s))),
                a.attr("aria-valuenow", e),
                f(t, a)
            }, g.refresh_speed)
        }, g.transition_delay))
    }
    ;
    var t = n.fn.progressbar;
    n.fn.progressbar = function(s) {
        return this.each(function() {
            var t = n(this)
              , e = t.data("bs.progressbar")
              , i = "object" == typeof s && s;
            e && i && n.extend(e.options, i),
            e || t.data("bs.progressbar", e = new v(this,i)),
            e.transition()
        })
    }
    ,
    n.fn.progressbar.Constructor = v,
    n.fn.progressbar.noConflict = function() {
        return n.fn.progressbar = t,
        this
    }
}(window.jQuery),
function(_, L, E) {
    var t;
    t = function(H) {
        "use strict";
        var v, k, y, I, W, j, l, w, t, r, g, q, h, e, P, A, o, a, p, u, C, s, c, d, n, f = {}, m = 0, i = function() {
            return {
                common: {
                    type: "line",
                    lineColor: "#00f",
                    fillColor: "#cdf",
                    defaultPixelsPerValue: 3,
                    width: "auto",
                    height: "auto",
                    composite: !1,
                    tagValuesAttribute: "values",
                    tagOptionsPrefix: "spark",
                    enableTagOptions: !1,
                    enableHighlight: !0,
                    highlightLighten: 1.4,
                    tooltipSkipNull: !0,
                    tooltipPrefix: "",
                    tooltipSuffix: "",
                    disableHiddenCheck: !1,
                    numberFormatter: !1,
                    numberDigitGroupCount: 3,
                    numberDigitGroupSep: ",",
                    numberDecimalMark: ".",
                    disableTooltips: !1,
                    disableInteraction: !1
                },
                line: {
                    spotColor: "#f80",
                    highlightSpotColor: "#5f5",
                    highlightLineColor: "#f22",
                    spotRadius: 1.5,
                    minSpotColor: "#f80",
                    maxSpotColor: "#f80",
                    lineWidth: 1,
                    normalRangeMin: E,
                    normalRangeMax: E,
                    normalRangeColor: "#ccc",
                    drawNormalOnTop: !1,
                    chartRangeMin: E,
                    chartRangeMax: E,
                    chartRangeMinX: E,
                    chartRangeMaxX: E,
                    tooltipFormat: new v('<span style="color: {{color}}">&#9679;</span> {{prefix}}{{y}}{{suffix}}')
                },
                bar: {
                    barColor: "#3366cc",
                    negBarColor: "#f44",
                    stackedBarColor: ["#3366cc", "#dc3912", "#ff9900", "#109618", "#66aa00", "#dd4477", "#0099c6", "#990099"],
                    zeroColor: E,
                    nullColor: E,
                    zeroAxis: !0,
                    barWidth: 4,
                    barSpacing: 1,
                    chartRangeMax: E,
                    chartRangeMin: E,
                    chartRangeClip: !1,
                    colorMap: E,
                    tooltipFormat: new v('<span style="color: {{color}}">&#9679;</span> {{prefix}}{{value}}{{suffix}}')
                },
                tristate: {
                    barWidth: 4,
                    barSpacing: 1,
                    posBarColor: "#6f6",
                    negBarColor: "#f44",
                    zeroBarColor: "#999",
                    colorMap: {},
                    tooltipFormat: new v('<span style="color: {{color}}">&#9679;</span> {{value:map}}'),
                    tooltipValueLookups: {
                        map: {
                            "-1": "Loss",
                            0: "Draw",
                            1: "Win"
                        }
                    }
                },
                discrete: {
                    lineHeight: "auto",
                    thresholdColor: E,
                    thresholdValue: 0,
                    chartRangeMax: E,
                    chartRangeMin: E,
                    chartRangeClip: !1,
                    tooltipFormat: new v("{{prefix}}{{value}}{{suffix}}")
                },
                bullet: {
                    targetColor: "#f33",
                    targetWidth: 3,
                    performanceColor: "#33f",
                    rangeColors: ["#d3dafe", "#a8b6ff", "#7f94ff"],
                    base: E,
                    tooltipFormat: new v("{{fieldkey:fields}} - {{value}}"),
                    tooltipValueLookups: {
                        fields: {
                            r: "Range",
                            p: "Performance",
                            t: "Target"
                        }
                    }
                },
                pie: {
                    offset: 0,
                    sliceColors: ["#3366cc", "#dc3912", "#ff9900", "#109618", "#66aa00", "#dd4477", "#0099c6", "#990099"],
                    borderWidth: 0,
                    borderColor: "#000",
                    tooltipFormat: new v('<span style="color: {{color}}">&#9679;</span> {{value}} ({{percent.1}}%)')
                },
                box: {
                    raw: !1,
                    boxLineColor: "#000",
                    boxFillColor: "#cdf",
                    whiskerColor: "#000",
                    outlierLineColor: "#333",
                    outlierFillColor: "#fff",
                    medianColor: "#f00",
                    showOutliers: !0,
                    outlierIQR: 1.5,
                    spotRadius: 1.5,
                    target: E,
                    targetColor: "#4a2",
                    chartRangeMax: E,
                    chartRangeMin: E,
                    tooltipFormat: new v("{{field:fields}}: {{value}}"),
                    tooltipFormatFieldlistKey: "field",
                    tooltipValueLookups: {
                        fields: {
                            lq: "Lower Quartile",
                            med: "Median",
                            uq: "Upper Quartile",
                            lo: "Left Outlier",
                            ro: "Right Outlier",
                            lw: "Left Whisker",
                            rw: "Right Whisker"
                        }
                    }
                }
            }
        }, x = function() {
            var t, e = function() {
                this.init.apply(this, arguments)
            };
            return 1 < arguments.length ? (arguments[0] ? (e.prototype = H.extend(new arguments[0], arguments[arguments.length - 1]),
            e._super = arguments[0].prototype) : e.prototype = arguments[arguments.length - 1],
            2 < arguments.length && ((t = Array.prototype.slice.call(arguments, 1, -1)).unshift(e.prototype),
            H.extend.apply(H, t))) : e.prototype = arguments[0],
            e.prototype.cls = e
        };
        H.SPFormatClass = v = x({
            fre: /\{\{([\w.]+?)(:(.+?))?\}\}/g,
            precre: /(\w+)\.(\d+)/,
            init: function(t, e) {
                this.format = t,
                this.fclass = e
            },
            render: function(t, e, i) {
                var s, n, r, a, o = this, h = t;
                return this.format.replace(this.fre, function() {
                    return r = arguments[1],
                    n = arguments[3],
                    (s = o.precre.exec(r)) ? (a = s[2],
                    r = s[1]) : a = !1,
                    (r = h[r]) === E ? "" : n && e && e[n] ? e[n].get ? e[n].get(r) || r : e[n][r] || r : r = l(r) ? i.get("numberFormatter") ? i.get("numberFormatter")(r) : g(r, a, i.get("numberDigitGroupCount"), i.get("numberDigitGroupSep"), i.get("numberDecimalMark")) : r
                })
            }
        }),
        H.spformat = function(t, e) {
            return new v(t,e)
        }
        ,
        k = function(t, e, i) {
            return t < e ? e : i < t ? i : t
        }
        ,
        y = function(t, e) {
            var i;
            return 2 === e ? (i = L.floor(t.length / 2),
            t.length % 2 ? t[i] : (t[i - 1] + t[i]) / 2) : t.length % 2 ? (i = (t.length * e + e) / 4) % 1 ? (t[L.floor(i)] + t[L.floor(i) - 1]) / 2 : t[i - 1] : (i = (t.length * e + 2) / 4) % 1 ? (t[L.floor(i)] + t[L.floor(i) - 1]) / 2 : t[i - 1]
        }
        ,
        I = function(t) {
            var e;
            switch (t) {
            case "undefined":
                t = E;
                break;
            case "null":
                t = null;
                break;
            case "true":
                t = !0;
                break;
            case "false":
                t = !1;
                break;
            default:
                t == (e = parseFloat(t)) && (t = e)
            }
            return t
        }
        ,
        W = function(t) {
            for (var e = [], i = t.length; i--; )
                e[i] = I(t[i]);
            return e
        }
        ,
        j = function(t, e) {
            for (var i = [], s = 0, n = t.length; s < n; s++)
                t[s] !== e && i.push(t[s]);
            return i
        }
        ,
        l = function(t) {
            return !isNaN(parseFloat(t)) && isFinite(t)
        }
        ,
        g = function(t, e, i, s, n) {
            var r;
            for (t = (!1 === e ? parseFloat(t).toString() : t.toFixed(e)).split(""),
            (e = (e = H.inArray(".", t)) < 0 ? t.length : e) < t.length && (t[e] = n),
            r = e - i; 0 < r; r -= i)
                t.splice(r, 0, s);
            return t.join("")
        }
        ,
        w = function(t, e, i) {
            for (var s = e.length; s--; )
                if ((!i || null !== e[s]) && e[s] !== t)
                    return !1;
            return !0
        }
        ,
        r = function(t) {
            return H.isArray(t) ? t : [t]
        }
        ,
        t = function(t) {
            var e, i;
            if (_.createStyleSheet)
                try {
                    return void (_.createStyleSheet().cssText = t)
                } catch (t) {
                    i = !0
                }
            (e = _.createElement("style")).type = "text/css",
            _.getElementsByTagName("head")[0].appendChild(e),
            i ? _.styleSheets[_.styleSheets.length - 1].cssText = t : e["string" == typeof _.body.style.WebkitAppearance ? "innerText" : "innerHTML"] = t
        }
        ,
        H.fn.simpledraw = function(t, e, i, s) {
            var n;
            if (i && (n = this.data("_jqs_vcanvas")))
                return n;
            if (!1 === H.fn.sparkline.canvas)
                return !1;
            if (H.fn.sparkline.canvas === E) {
                i = _.createElement("canvas");
                if (i.getContext && i.getContext("2d"))
                    H.fn.sparkline.canvas = function(t, e, i, s) {
                        return new c(t,e,i,s)
                    }
                    ;
                else {
                    if (!_.namespaces || _.namespaces.v)
                        return H.fn.sparkline.canvas = !1;
                    _.namespaces.add("v", "urn:schemas-microsoft-com:vml", "#default#VML"),
                    H.fn.sparkline.canvas = function(t, e, i, s) {
                        return new d(t,e,i)
                    }
                }
            }
            return t === E && (t = H(this).innerWidth()),
            e === E && (e = H(this).innerHeight()),
            n = H.fn.sparkline.canvas(t, e, this, s),
            (s = H(this).data("_jqs_mhandler")) && s.registerCanvas(n),
            n
        }
        ,
        H.fn.cleardraw = function() {
            var t = this.data("_jqs_vcanvas");
            t && t.reset()
        }
        ,
        H.RangeMapClass = q = x({
            init: function(t) {
                var e, i, s = [];
                for (e in t)
                    t.hasOwnProperty(e) && "string" == typeof e && -1 < e.indexOf(":") && ((i = e.split(":"))[0] = 0 === i[0].length ? -1 / 0 : parseFloat(i[0]),
                    i[1] = 0 === i[1].length ? 1 / 0 : parseFloat(i[1]),
                    i[2] = t[e],
                    s.push(i));
                this.map = t,
                this.rangelist = s || !1
            },
            get: function(t) {
                var e, i, s, n = this.rangelist;
                if ((s = this.map[t]) !== E)
                    return s;
                if (n)
                    for (e = n.length; e--; )
                        if ((i = n[e])[0] <= t && i[1] >= t)
                            return i[2];
                return E
            }
        }),
        H.range_map = function(t) {
            return new q(t)
        }
        ,
        h = x({
            init: function(t, e) {
                var i = H(t);
                this.$el = i,
                this.options = e,
                this.currentPageX = 0,
                this.currentPageY = 0,
                this.el = t,
                this.splist = [],
                this.tooltip = null,
                this.over = !1,
                this.displayTooltips = !e.get("disableTooltips"),
                this.highlightEnabled = !e.get("disableHighlight")
            },
            registerSparkline: function(t) {
                this.splist.push(t),
                this.over && this.updateDisplay()
            },
            registerCanvas: function(t) {
                var e = H(t.canvas);
                this.canvas = t,
                (this.$canvas = e).mouseenter(H.proxy(this.mouseenter, this)),
                e.mouseleave(H.proxy(this.mouseleave, this)),
                e.click(H.proxy(this.mouseclick, this))
            },
            reset: function(t) {
                this.splist = [],
                this.tooltip && t && (this.tooltip.remove(),
                this.tooltip = E)
            },
            mouseclick: function(t) {
                var e = H.Event("sparklineClick");
                e.originalEvent = t,
                e.sparklines = this.splist,
                this.$el.trigger(e)
            },
            mouseenter: function(t) {
                H(_.body).unbind("mousemove.jqs"),
                H(_.body).bind("mousemove.jqs", H.proxy(this.mousemove, this)),
                this.over = !0,
                this.currentPageX = t.pageX,
                this.currentPageY = t.pageY,
                this.currentEl = t.target,
                !this.tooltip && this.displayTooltips && (this.tooltip = new e(this.options),
                this.tooltip.updatePosition(t.pageX, t.pageY)),
                this.updateDisplay()
            },
            mouseleave: function() {
                H(_.body).unbind("mousemove.jqs");
                var t, e = this.splist, i = e.length, s = !1;
                for (this.over = !1,
                this.currentEl = null,
                this.tooltip && (this.tooltip.remove(),
                this.tooltip = null),
                t = 0; t < i; t++)
                    e[t].clearRegionHighlight() && (s = !0);
                s && this.canvas.render()
            },
            mousemove: function(t) {
                this.currentPageX = t.pageX,
                this.currentPageY = t.pageY,
                this.currentEl = t.target,
                this.tooltip && this.tooltip.updatePosition(t.pageX, t.pageY),
                this.updateDisplay()
            },
            updateDisplay: function() {
                var t, e, i, s = this.splist, n = s.length, r = !1, a = this.$canvas.offset(), o = this.currentPageX - a.left, h = this.currentPageY - a.top;
                if (this.over) {
                    for (e = 0; e < n; e++)
                        (i = s[e].setRegionHighlight(this.currentEl, o, h)) && (r = !0);
                    if (r) {
                        if ((a = H.Event("sparklineRegionChange")).sparklines = this.splist,
                        this.$el.trigger(a),
                        this.tooltip) {
                            for (t = "",
                            e = 0; e < n; e++)
                                t += s[e].getCurrentRegionTooltip();
                            this.tooltip.setContent(t)
                        }
                        this.disableHighlight || this.canvas.render()
                    }
                    null === i && this.mouseleave()
                }
            }
        }),
        e = x({
            sizeStyle: "position: static !important;display: block !important;visibility: hidden !important;float: left !important;",
            init: function(t) {
                var e = t.get("tooltipClassname", "jqstooltip")
                  , i = this.sizeStyle;
                this.container = t.get("tooltipContainer") || _.body,
                this.tooltipOffsetX = t.get("tooltipOffsetX", 10),
                this.tooltipOffsetY = t.get("tooltipOffsetY", 12),
                H("#jqssizetip").remove(),
                H("#jqstooltip").remove(),
                this.sizetip = H("<div/>", {
                    id: "jqssizetip",
                    style: i,
                    class: e
                }),
                this.tooltip = H("<div/>", {
                    id: "jqstooltip",
                    class: e
                }).appendTo(this.container),
                e = this.tooltip.offset(),
                this.offsetLeft = e.left,
                this.offsetTop = e.top,
                this.hidden = !0,
                H(window).unbind("resize.jqs scroll.jqs"),
                H(window).bind("resize.jqs scroll.jqs", H.proxy(this.updateWindowDims, this)),
                this.updateWindowDims()
            },
            updateWindowDims: function() {
                this.scrollTop = H(window).scrollTop(),
                this.scrollLeft = H(window).scrollLeft(),
                this.scrollRight = this.scrollLeft + H(window).width(),
                this.updatePosition()
            },
            getSize: function(t) {
                this.sizetip.html(t).appendTo(this.container),
                this.width = this.sizetip.width() + 1,
                this.height = this.sizetip.height(),
                this.sizetip.remove()
            },
            setContent: function(t) {
                if (!t)
                    return this.tooltip.css("visibility", "hidden"),
                    void (this.hidden = !0);
                this.getSize(t),
                this.tooltip.html(t).css({
                    width: this.width,
                    height: this.height,
                    visibility: "visible"
                }),
                this.hidden && (this.hidden = !1,
                this.updatePosition())
            },
            updatePosition: function(t, e) {
                if (t === E) {
                    if (this.mousex === E)
                        return;
                    t = this.mousex - this.offsetLeft,
                    e = this.mousey - this.offsetTop
                } else
                    this.mousex = t -= this.offsetLeft,
                    this.mousey = e -= this.offsetTop;
                this.height && this.width && !this.hidden && (e -= this.height + this.tooltipOffsetY,
                t += this.tooltipOffsetX,
                e < this.scrollTop && (e = this.scrollTop),
                t < this.scrollLeft ? t = this.scrollLeft : t + this.width > this.scrollRight && (t = this.scrollRight - this.width),
                this.tooltip.css({
                    left: t,
                    top: e
                }))
            },
            remove: function() {
                this.tooltip.remove(),
                this.sizetip.remove(),
                this.sizetip = this.tooltip = E,
                H(window).unbind("resize.jqs scroll.jqs")
            }
        }),
        H(function() {
            t('.jqstooltip { position: absolute;left: 0px;top: 0px;visibility: hidden;background: rgb(0, 0, 0) transparent;background-color: rgba(0,0,0,0.6);filter:progid:DXImageTransform.Microsoft.gradient(startColorstr=#99000000, endColorstr=#99000000);-ms-filter: "progid:DXImageTransform.Microsoft.gradient(startColorstr=#99000000, endColorstr=#99000000)";color: white;font: 10px arial, san serif;text-align: left;white-space: nowrap;padding: 5px;border: 1px solid white;box-sizing: content-box;z-index: 10000;}.jqsfield { color: white;font: 10px arial, san serif;text-align: left;}')
        }),
        n = [],
        H.fn.sparkline = function(o, i) {
            return this.each(function() {
                var t, r = new H.fn.sparkline.options(this,i), a = H(this), e = function() {
                    var t, e, i, s = "html" === o || o === E ? (i = (i = this.getAttribute(r.get("tagValuesAttribute"))) === E || null === i ? a.html() : i).replace(/(^\s*<!--)|(-->\s*$)|\s+/g, "").split(",") : o, n = "auto" === r.get("width") ? s.length * r.get("defaultPixelsPerValue") : r.get("width");
                    "auto" === r.get("height") ? r.get("composite") && H.data(this, "_jqs_vcanvas") || ((i = _.createElement("span")).innerHTML = "a",
                    a.html(i),
                    e = H(i).innerHeight() || H(i).height(),
                    H(i).remove(),
                    i = null) : e = r.get("height"),
                    r.get("disableInteraction") ? t = !1 : (t = H.data(this, "_jqs_mhandler")) ? r.get("composite") || t.reset() : (t = new h(this,r),
                    H.data(this, "_jqs_mhandler", t)),
                    !r.get("composite") || H.data(this, "_jqs_vcanvas") ? ((e = new H.fn.sparkline[r.get("type")](this,s,r,n,e)).render(),
                    t && t.registerSparkline(e)) : H.data(this, "_jqs_errnotify") || (alert("Attempted to attach a composite sparkline to an element with no existing sparkline"),
                    H.data(this, "_jqs_errnotify", !0))
                };
                if (H(this).html() && !r.get("disableHiddenCheck") && H(this).is(":hidden") || !H(this).parents("body").length) {
                    if (!r.get("composite") && H.data(this, "_jqs_pending"))
                        for (t = n.length; t; t--)
                            n[t - 1][0] == this && n.splice(t - 1, 1);
                    n.push([this, e]),
                    H.data(this, "_jqs_pending", !0)
                } else
                    e.call(this)
            })
        }
        ,
        H.fn.sparkline.defaults = i(),
        H.sparkline_display_visible = function() {
            for (var t, e = [], i = 0, s = n.length; i < s; i++)
                t = n[i][0],
                H(t).is(":visible") && !H(t).parents().is(":hidden") ? (n[i][1].call(t),
                H.data(n[i][0], "_jqs_pending", !1),
                e.push(i)) : H(t).closest("html").length || H.data(t, "_jqs_pending") || (H.data(n[i][0], "_jqs_pending", !1),
                e.push(i));
            for (i = e.length; i; i--)
                n.splice(e[i - 1], 1)
        }
        ,
        H.fn.sparkline.options = x({
            init: function(t, e) {
                var i, s;
                this.userOptions = e = e || {},
                this.tag = t,
                this.tagValCache = {},
                s = (i = H.fn.sparkline.defaults).common,
                this.tagOptionsPrefix = e.enableTagOptions && (e.tagOptionsPrefix || s.tagOptionsPrefix),
                t = (t = this.getTagSetting("type")) === f ? i[e.type || s.type] : i[t],
                this.mergedOptions = H.extend({}, s, t, e)
            },
            getTagSetting: function(t) {
                var e, i, s, n, r = this.tagOptionsPrefix;
                if (!1 === r || r === E)
                    return f;
                if (this.tagValCache.hasOwnProperty(t))
                    e = this.tagValCache.key;
                else {
                    if ((e = this.tag.getAttribute(r + t)) === E || null === e)
                        e = f;
                    else if ("[" === e.substr(0, 1))
                        for (i = (e = e.substr(1, e.length - 2).split(",")).length; i--; )
                            e[i] = I(e[i].replace(/(^\s*)|(\s*$)/g, ""));
                    else if ("{" === e.substr(0, 1))
                        for (s = e.substr(1, e.length - 2).split(","),
                        e = {},
                        i = s.length; i--; )
                            e[(n = s[i].split(":", 2))[0].replace(/(^\s*)|(\s*$)/g, "")] = I(n[1].replace(/(^\s*)|(\s*$)/g, ""));
                    else
                        e = I(e);
                    this.tagValCache.key = e
                }
                return e
            },
            get: function(t, e) {
                var i = this.getTagSetting(t);
                return i !== f ? i : (t = this.mergedOptions[t]) === E ? e : t
            }
        }),
        H.fn.sparkline._base = x({
            disabled: !1,
            init: function(t, e, i, s, n) {
                this.el = t,
                this.$el = H(t),
                this.values = e,
                this.options = i,
                this.width = s,
                this.height = n,
                this.currentRegion = E
            },
            initTarget: function() {
                var t = !this.options.get("disableInteraction");
                (this.target = this.$el.simpledraw(this.width, this.height, this.options.get("composite"), t)) ? (this.canvasWidth = this.target.pixelWidth,
                this.canvasHeight = this.target.pixelHeight) : this.disabled = !0
            },
            render: function() {
                return !this.disabled || (this.el.innerHTML = "",
                !1)
            },
            getRegion: function(t, e) {},
            setRegionHighlight: function(t, e, i) {
                var s = this.currentRegion
                  , n = !this.options.get("disableHighlight");
                return e > this.canvasWidth || i > this.canvasHeight || e < 0 || i < 0 ? null : s !== (i = this.getRegion(t, e, i)) && (s !== E && n && this.removeHighlight(),
                (this.currentRegion = i) !== E && n && this.renderHighlight(),
                !0)
            },
            clearRegionHighlight: function() {
                return this.currentRegion !== E && (this.removeHighlight(),
                !(this.currentRegion = E))
            },
            renderHighlight: function() {
                this.changeHighlight(!0)
            },
            removeHighlight: function() {
                this.changeHighlight(!1)
            },
            changeHighlight: function(t) {},
            getCurrentRegionTooltip: function() {
                var t, e, i, s, n, r, a, o, h, l, g, p, u, c, d = this.options, f = "", m = [];
                if (this.currentRegion === E)
                    return "";
                if (t = this.getCurrentRegionFields(),
                g = d.get("tooltipFormatter"))
                    return g(this, d, t);
                if (d.get("tooltipChartTitle") && (f += '<div class="jqs jqstitle">' + d.get("tooltipChartTitle") + "</div>\n"),
                !(e = this.options.get("tooltipFormat")))
                    return "";
                if (H.isArray(e) || (e = [e]),
                H.isArray(t) || (t = [t]),
                a = this.options.get("tooltipFormatFieldlist"),
                o = this.options.get("tooltipFormatFieldlistKey"),
                a && o) {
                    for (h = [],
                    r = t.length; r--; )
                        l = t[r][o],
                        -1 != (c = H.inArray(l, a)) && (h[c] = t[r]);
                    t = h
                }
                for (i = e.length,
                u = t.length,
                r = 0; r < i; r++)
                    for (s = (p = "string" == typeof (p = e[r]) ? new v(p) : p).fclass || "jqsfield",
                    c = 0; c < u; c++)
                        t[c].isNull && d.get("tooltipSkipNull") || (H.extend(t[c], {
                            prefix: d.get("tooltipPrefix"),
                            suffix: d.get("tooltipSuffix")
                        }),
                        n = p.render(t[c], d.get("tooltipValueLookups"), d),
                        m.push('<div class="' + s + '">' + n + "</div>"));
                return m.length ? f + m.join("\n") : ""
            },
            getCurrentRegionFields: function() {},
            calcHighlightColor: function(t, e) {
                var i, s, n, r, a = e.get("highlightColor"), o = e.get("highlightLighten");
                if (a)
                    return a;
                if (o && (i = /^#([0-9a-f])([0-9a-f])([0-9a-f])$/i.exec(t) || /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(t))) {
                    for (n = [],
                    s = 4 === t.length ? 16 : 1,
                    r = 0; r < 3; r++)
                        n[r] = k(L.round(parseInt(i[r + 1], 16) * s * o), 0, 255);
                    return "rgb(" + n.join(",") + ")"
                }
                return t
            }
        }),
        i = {
            changeHighlight: function(t) {
                var e = this.currentRegion
                  , i = this.target
                  , s = this.regionShapes[e];
                s && (t = this.renderRegion(e, t),
                H.isArray(t) || H.isArray(s) ? (i.replaceWithShapes(s, t),
                this.regionShapes[e] = H.map(t, function(t) {
                    return t.id
                })) : (i.replaceWithShape(s, t),
                this.regionShapes[e] = t.id))
            },
            render: function() {
                var t, e, i, s, n = this.values, r = this.target, a = this.regionShapes;
                if (this.cls._super.render.call(this)) {
                    for (i = n.length; i--; )
                        if (t = this.renderRegion(i))
                            if (H.isArray(t)) {
                                for (e = [],
                                s = t.length; s--; )
                                    t[s].append(),
                                    e.push(t[s].id);
                                a[i] = e
                            } else
                                t.append(),
                                a[i] = t.id;
                        else
                            a[i] = null;
                    r.render()
                }
            }
        },
        H.fn.sparkline.line = P = x(H.fn.sparkline._base, {
            type: "line",
            init: function(t, e, i, s, n) {
                P._super.init.call(this, t, e, i, s, n),
                this.vertices = [],
                this.regionMap = [],
                this.xvalues = [],
                this.yvalues = [],
                this.yminmax = [],
                this.hightlightSpotId = null,
                this.lastShapeId = null,
                this.initTarget()
            },
            getRegion: function(t, e, i) {
                for (var s = this.regionMap, n = s.length; n--; )
                    if (null !== s[n] && e >= s[n][0] && e <= s[n][1])
                        return s[n][2];
                return E
            },
            getCurrentRegionFields: function() {
                var t = this.currentRegion;
                return {
                    isNull: null === this.yvalues[t],
                    x: this.xvalues[t],
                    y: this.yvalues[t],
                    color: this.options.get("lineColor"),
                    fillColor: this.options.get("fillColor"),
                    offset: t
                }
            },
            renderHighlight: function() {
                var t = this.currentRegion
                  , e = this.target
                  , i = this.vertices[t]
                  , s = this.options
                  , n = s.get("spotRadius")
                  , t = s.get("highlightSpotColor")
                  , s = s.get("highlightLineColor");
                i && (n && t && (t = e.drawCircle(i[0], i[1], n, E, t),
                this.highlightSpotId = t.id,
                e.insertAfterShape(this.lastShapeId, t)),
                s && (s = e.drawLine(i[0], this.canvasTop, i[0], this.canvasTop + this.canvasHeight, s),
                this.highlightLineId = s.id,
                e.insertAfterShape(this.lastShapeId, s)))
            },
            removeHighlight: function() {
                var t = this.target;
                this.highlightSpotId && (t.removeShapeId(this.highlightSpotId),
                this.highlightSpotId = null),
                this.highlightLineId && (t.removeShapeId(this.highlightLineId),
                this.highlightLineId = null)
            },
            scanValues: function() {
                for (var t, e, i, s, n = this.values, r = n.length, a = this.xvalues, o = this.yvalues, h = this.yminmax, l = 0; l < r; l++)
                    t = n[l],
                    e = "string" == typeof n[l],
                    i = "object" == typeof n[l] && n[l]instanceof Array,
                    s = e && n[l].split(":"),
                    e && 2 === s.length ? (a.push(Number(s[0])),
                    o.push(Number(s[1])),
                    h.push(Number(s[1]))) : i ? (a.push(t[0]),
                    o.push(t[1]),
                    h.push(t[1])) : (a.push(l),
                    null === n[l] || "null" === n[l] ? o.push(null) : (o.push(Number(t)),
                    h.push(Number(t))));
                this.options.get("xvalues") && (a = this.options.get("xvalues")),
                this.maxy = this.maxyorg = L.max.apply(L, h),
                this.miny = this.minyorg = L.min.apply(L, h),
                this.maxx = L.max.apply(L, a),
                this.minx = L.min.apply(L, a),
                this.xvalues = a,
                this.yvalues = o,
                this.yminmax = h
            },
            processRangeOptions: function() {
                var t = this.options
                  , e = t.get("normalRangeMin")
                  , i = t.get("normalRangeMax");
                e !== E && (e < this.miny && (this.miny = e),
                i > this.maxy && (this.maxy = i)),
                t.get("chartRangeMin") !== E && (t.get("chartRangeClip") || t.get("chartRangeMin") < this.miny) && (this.miny = t.get("chartRangeMin")),
                t.get("chartRangeMax") !== E && (t.get("chartRangeClip") || t.get("chartRangeMax") > this.maxy) && (this.maxy = t.get("chartRangeMax")),
                t.get("chartRangeMinX") !== E && (t.get("chartRangeClipX") || t.get("chartRangeMinX") < this.minx) && (this.minx = t.get("chartRangeMinX")),
                t.get("chartRangeMaxX") !== E && (t.get("chartRangeClipX") || t.get("chartRangeMaxX") > this.maxx) && (this.maxx = t.get("chartRangeMaxX"))
            },
            drawNormalRange: function(t, e, i, s, n) {
                var r = this.options.get("normalRangeMin")
                  , a = this.options.get("normalRangeMax")
                  , e = e + L.round(i - i * ((a - this.miny) / n))
                  , n = L.round(i * (a - r) / n);
                this.target.drawRect(t, e, s, n, E, this.options.get("normalRangeColor")).append()
            },
            render: function() {
                var t, e, i, s, n, r, a, o, h, l, g, p, u, c, d, f, m, v, x, y, C, _, w = this.options, b = this.target, S = this.canvasWidth, R = this.canvasHeight, T = this.vertices, M = w.get("spotRadius"), k = this.regionMap;
                if (P._super.render.call(this) && (this.scanValues(),
                this.processRangeOptions(),
                y = this.xvalues,
                C = this.yvalues,
                this.yminmax.length && !(this.yvalues.length < 2))) {
                    for (s = n = 0,
                    t = this.maxx - this.minx == 0 ? 1 : this.maxx - this.minx,
                    e = this.maxy - this.miny == 0 ? 1 : this.maxy - this.miny,
                    i = this.yvalues.length - 1,
                    (M = M && (S < 4 * M || R < 4 * M) ? 0 : M) && (((v = w.get("highlightSpotColor") && !w.get("disableInteraction")) || w.get("minSpotColor") || w.get("spotColor") && C[i] === this.miny) && (R -= L.ceil(M)),
                    (v || w.get("maxSpotColor") || w.get("spotColor") && C[i] === this.maxy) && (R -= L.ceil(M),
                    s += L.ceil(M)),
                    !v && (!w.get("minSpotColor") && !w.get("maxSpotColor") || C[0] !== this.miny && C[0] !== this.maxy) || (n += L.ceil(M),
                    S -= L.ceil(M)),
                    (v || w.get("spotColor") || w.get("minSpotColor") || w.get("maxSpotColor") && (C[i] === this.miny || C[i] === this.maxy)) && (S -= L.ceil(M))),
                    R--,
                    w.get("normalRangeMin") === E || w.get("drawNormalOnTop") || this.drawNormalRange(n, s, R, S, e),
                    a = [r = []],
                    g = null,
                    u = C.length,
                    _ = 0; _ < u; _++)
                        o = y[_],
                        p = y[_ + 1],
                        h = C[_],
                        l = n + L.round((o - this.minx) * (S / t)),
                        p = _ < u - 1 ? n + L.round((p - this.minx) * (S / t)) : S,
                        k[_] = [g || 0, p = l + (p - l) / 2, _],
                        g = p,
                        null === h ? _ && (null !== C[_ - 1] && a.push(r = []),
                        T.push(null)) : ((h = h < this.miny ? this.miny : h) > this.maxy && (h = this.maxy),
                        r.length || r.push([l, s + R]),
                        h = [l, s + L.round(R - R * ((h - this.miny) / e))],
                        r.push(h),
                        T.push(h));
                    for (c = [],
                    d = [],
                    f = a.length,
                    _ = 0; _ < f; _++)
                        (r = a[_]).length && (w.get("fillColor") && (r.push([r[r.length - 1][0], s + R]),
                        d.push(r.slice(0)),
                        r.pop()),
                        2 < r.length && (r[0] = [r[0][0], r[1][1]]),
                        c.push(r));
                    for (f = d.length,
                    _ = 0; _ < f; _++)
                        b.drawShape(d[_], w.get("fillColor"), w.get("fillColor")).append();
                    for (w.get("normalRangeMin") !== E && w.get("drawNormalOnTop") && this.drawNormalRange(n, s, R, S, e),
                    f = c.length,
                    _ = 0; _ < f; _++)
                        b.drawShape(c[_], w.get("lineColor"), E, w.get("lineWidth")).append();
                    if (M && w.get("valueSpots"))
                        for ((m = w.get("valueSpots")).get === E && (m = new q(m)),
                        _ = 0; _ < u; _++)
                            (x = m.get(C[_])) && b.drawCircle(n + L.round((y[_] - this.minx) * (S / t)), s + L.round(R - R * ((C[_] - this.miny) / e)), M, E, x).append();
                    M && w.get("spotColor") && null !== C[i] && b.drawCircle(n + L.round((y[y.length - 1] - this.minx) * (S / t)), s + L.round(R - R * ((C[i] - this.miny) / e)), M, E, w.get("spotColor")).append(),
                    this.maxy !== this.minyorg && (M && w.get("minSpotColor") && (o = y[H.inArray(this.minyorg, C)],
                    b.drawCircle(n + L.round((o - this.minx) * (S / t)), s + L.round(R - R * ((this.minyorg - this.miny) / e)), M, E, w.get("minSpotColor")).append()),
                    M && w.get("maxSpotColor") && (o = y[H.inArray(this.maxyorg, C)],
                    b.drawCircle(n + L.round((o - this.minx) * (S / t)), s + L.round(R - R * ((this.maxyorg - this.miny) / e)), M, E, w.get("maxSpotColor")).append())),
                    this.lastShapeId = b.getLastShapeId(),
                    this.canvasTop = s,
                    b.render()
                }
            }
        }),
        H.fn.sparkline.bar = A = x(H.fn.sparkline._base, i, {
            type: "bar",
            init: function(t, e, i, s, n) {
                var r, a, o, h, l, g, p, u, c, d, f = parseInt(i.get("barWidth"), 10), m = parseInt(i.get("barSpacing"), 10), v = i.get("chartRangeMin"), x = i.get("chartRangeMax"), y = i.get("chartRangeClip"), C = 1 / 0, _ = -1 / 0;
                for (A._super.init.call(this, t, e, i, s, n),
                T = 0,
                M = e.length; T < M; T++)
                    ((r = "string" == typeof (c = e[T]) && -1 < c.indexOf(":")) || H.isArray(c)) && (h = !0,
                    r && (c = e[T] = W(c.split(":"))),
                    c = j(c, null),
                    (r = L.min.apply(L, c)) < C && (C = r),
                    _ < (r = L.max.apply(L, c)) && (_ = r));
                this.stacked = h,
                this.regionShapes = {},
                this.barWidth = f,
                this.barSpacing = m,
                this.totalBarWidth = f + m,
                this.width = s = e.length * f + (e.length - 1) * m,
                this.initTarget(),
                y && (a = v === E ? -1 / 0 : v,
                o = x === E ? 1 / 0 : x);
                for (var w = [], b = h ? [] : w, S = [], R = [], T = 0, M = e.length; T < M; T++)
                    if (h)
                        for (l = e[T],
                        e[T] = u = [],
                        S[T] = 0,
                        g = b[T] = R[T] = 0,
                        p = l.length; g < p; g++)
                            null !== (c = u[g] = y ? k(l[g], a, o) : l[g]) && (0 < c && (S[T] += c),
                            C < 0 && 0 < _ ? c < 0 ? R[T] += L.abs(c) : b[T] += c : b[T] += L.abs(c - (c < 0 ? _ : C)),
                            w.push(c));
                    else
                        c = y ? k(e[T], a, o) : e[T],
                        null !== (c = e[T] = I(c)) && w.push(c);
                this.max = f = L.max.apply(L, w),
                this.min = m = L.min.apply(L, w),
                this.stackMax = _ = h ? L.max.apply(L, S) : f,
                this.stackMin = C = h ? L.min.apply(L, w) : m,
                i.get("chartRangeMin") !== E && (i.get("chartRangeClip") || i.get("chartRangeMin") < m) && (m = i.get("chartRangeMin")),
                i.get("chartRangeMax") !== E && (i.get("chartRangeClip") || i.get("chartRangeMax") > f) && (f = i.get("chartRangeMax")),
                this.zeroAxis = s = i.get("zeroAxis", !0),
                this.xaxisOffset = v = m <= 0 && 0 <= f && s ? 0 : 0 == s || 0 < m ? m : f,
                x = h ? L.max.apply(L, b) + L.max.apply(L, R) : f - m,
                this.canvasHeightEf = s && m < 0 ? this.canvasHeight - 2 : this.canvasHeight - 1,
                m < v ? (d = ((h && 0 <= f ? _ : f) - v) / x * this.canvasHeight) !== L.ceil(d) && (this.canvasHeightEf -= 2,
                d = L.ceil(d)) : d = this.canvasHeight,
                this.yoffset = d,
                H.isArray(i.get("colorMap")) ? (this.colorMapByIndex = i.get("colorMap"),
                this.colorMapByValue = null) : (this.colorMapByIndex = null,
                this.colorMapByValue = i.get("colorMap"),
                this.colorMapByValue && this.colorMapByValue.get === E && (this.colorMapByValue = new q(this.colorMapByValue))),
                this.range = x
            },
            getRegion: function(t, e, i) {
                e = L.floor(e / this.totalBarWidth);
                return e < 0 || e >= this.values.length ? E : e
            },
            getCurrentRegionFields: function() {
                for (var t, e = this.currentRegion, i = r(this.values[e]), s = [], n = i.length; n--; )
                    t = i[n],
                    s.push({
                        isNull: null === t,
                        value: t,
                        color: this.calcColor(n, t, e),
                        offset: e
                    });
                return s
            },
            calcColor: function(t, e, i) {
                var s, n = this.colorMapByIndex, r = this.colorMapByValue, a = this.options, o = this.stacked ? a.get("stackedBarColor") : e < 0 ? a.get("negBarColor") : a.get("barColor");
                return 0 === e && a.get("zeroColor") !== E && (o = a.get("zeroColor")),
                r && (s = r.get(e)) ? o = s : n && n.length > i && (o = n[i]),
                H.isArray(o) ? o[t % o.length] : o
            },
            renderRegion: function(t, e) {
                var i, s, n, r, a, o, h, l = this.values[t], g = this.options, p = this.xaxisOffset, u = [], c = this.range, d = this.stacked, f = this.target, m = t * this.totalBarWidth, v = this.canvasHeightEf, x = this.yoffset, y = (l = H.isArray(l) ? l : [l]).length, C = (l[0],
                w(null, l)), _ = w(p, l, !0);
                if (C)
                    return g.get("nullColor") ? (n = e ? g.get("nullColor") : this.calcHighlightColor(g.get("nullColor"), g),
                    f.drawRect(m, i = 0 < x ? x - 1 : x, this.barWidth - 1, 0, n, n)) : E;
                for (r = x,
                a = 0; a < y; a++) {
                    if (h = l[a],
                    d && h === p) {
                        if (!_ || o)
                            continue;
                        o = !0
                    }
                    s = 0 < c ? L.floor(v * (L.abs(h - p) / c)) + 1 : 1,
                    h < p || h === p && 0 === x ? (i = r,
                    r += s) : (i = x - s,
                    x -= s),
                    n = this.calcColor(a, h, t),
                    e && (n = this.calcHighlightColor(n, g)),
                    u.push(f.drawRect(m, i, this.barWidth - 1, s - 1, n, n))
                }
                return 1 === u.length ? u[0] : u
            }
        }),
        H.fn.sparkline.tristate = o = x(H.fn.sparkline._base, i, {
            type: "tristate",
            init: function(t, e, i, s, n) {
                var r = parseInt(i.get("barWidth"), 10)
                  , a = parseInt(i.get("barSpacing"), 10);
                o._super.init.call(this, t, e, i, s, n),
                this.regionShapes = {},
                this.barWidth = r,
                this.barSpacing = a,
                this.totalBarWidth = r + a,
                this.values = H.map(e, Number),
                this.width = s = e.length * r + (e.length - 1) * a,
                H.isArray(i.get("colorMap")) ? (this.colorMapByIndex = i.get("colorMap"),
                this.colorMapByValue = null) : (this.colorMapByIndex = null,
                this.colorMapByValue = i.get("colorMap"),
                this.colorMapByValue && this.colorMapByValue.get === E && (this.colorMapByValue = new q(this.colorMapByValue))),
                this.initTarget()
            },
            getRegion: function(t, e, i) {
                return L.floor(e / this.totalBarWidth)
            },
            getCurrentRegionFields: function() {
                var t = this.currentRegion;
                return {
                    isNull: this.values[t] === E,
                    value: this.values[t],
                    color: this.calcColor(this.values[t], t),
                    offset: t
                }
            },
            calcColor: function(t, e) {
                var i, s = this.values, n = this.options, r = this.colorMapByIndex, a = this.colorMapByValue, n = a && (i = a.get(t)) ? i : r && r.length > e ? r[e] : s[e] < 0 ? n.get("negBarColor") : 0 < s[e] ? n.get("posBarColor") : n.get("zeroBarColor");
                return n
            },
            renderRegion: function(t, e) {
                var i, s = this.values, n = this.options, r = this.target, a = r.pixelHeight, o = L.round(a / 2), a = t * this.totalBarWidth, o = s[t] < 0 ? (i = o) - 1 : 0 < s[t] ? (i = 0,
                o - 1) : (i = o - 1,
                2), t = this.calcColor(s[t], t);
                if (null !== t)
                    return e && (t = this.calcHighlightColor(t, n)),
                    r.drawRect(a, i, this.barWidth - 1, o - 1, t, t)
            }
        }),
        H.fn.sparkline.discrete = a = x(H.fn.sparkline._base, i, {
            type: "discrete",
            init: function(t, e, i, s, n) {
                a._super.init.call(this, t, e, i, s, n),
                this.regionShapes = {},
                this.values = e = H.map(e, Number),
                this.min = L.min.apply(L, e),
                this.max = L.max.apply(L, e),
                this.range = this.max - this.min,
                this.width = s = "auto" === i.get("width") ? 2 * e.length : this.width,
                this.interval = L.floor(s / e.length),
                this.itemWidth = s / e.length,
                i.get("chartRangeMin") !== E && (i.get("chartRangeClip") || i.get("chartRangeMin") < this.min) && (this.min = i.get("chartRangeMin")),
                i.get("chartRangeMax") !== E && (i.get("chartRangeClip") || i.get("chartRangeMax") > this.max) && (this.max = i.get("chartRangeMax")),
                this.initTarget(),
                this.target && (this.lineHeight = "auto" === i.get("lineHeight") ? L.round(.3 * this.canvasHeight) : i.get("lineHeight"))
            },
            getRegion: function(t, e, i) {
                return L.floor(e / this.itemWidth)
            },
            getCurrentRegionFields: function() {
                var t = this.currentRegion;
                return {
                    isNull: this.values[t] === E,
                    value: this.values[t],
                    offset: t
                }
            },
            renderRegion: function(t, e) {
                var i = this.values
                  , s = this.options
                  , n = this.min
                  , r = this.max
                  , a = this.range
                  , o = this.interval
                  , h = this.target
                  , l = this.canvasHeight
                  , g = this.lineHeight
                  , l = l - g
                  , r = k(i[t], n, r)
                  , o = t * o
                  , l = L.round(l - (r - n) / a * l)
                  , r = s.get("thresholdColor") && r < s.get("thresholdValue") ? s.get("thresholdColor") : s.get("lineColor");
                return e && (r = this.calcHighlightColor(r, s)),
                h.drawLine(o, l, o, l + g, r)
            }
        }),
        H.fn.sparkline.bullet = p = x(H.fn.sparkline._base, {
            type: "bullet",
            init: function(t, e, i, s, n) {
                var r;
                p._super.init.call(this, t, e, i, s, n),
                this.values = e = W(e),
                (r = e.slice())[0] = null === r[0] ? r[2] : r[0],
                r[1] = null === e[1] ? r[2] : r[1],
                t = L.min.apply(L, e),
                r = L.max.apply(L, e),
                t = i.get("base") === E ? t < 0 ? t : 0 : i.get("base"),
                this.min = t,
                this.max = r,
                this.range = r - t,
                this.shapes = {},
                this.valueShapes = {},
                this.regiondata = {},
                this.width = s = "auto" === i.get("width") ? "4.0em" : s,
                this.target = this.$el.simpledraw(s, n, i.get("composite")),
                e.length || (this.disabled = !0),
                this.initTarget()
            },
            getRegion: function(t, e, i) {
                i = this.target.getShapeAt(t, e, i);
                return i !== E && this.shapes[i] !== E ? this.shapes[i] : E
            },
            getCurrentRegionFields: function() {
                var t = this.currentRegion;
                return {
                    fieldkey: t.substr(0, 1),
                    value: this.values[t.substr(1)],
                    region: t
                }
            },
            changeHighlight: function(t) {
                var e, i = this.currentRegion, s = this.valueShapes[i];
                switch (delete this.shapes[s],
                i.substr(0, 1)) {
                case "r":
                    e = this.renderRange(i.substr(1), t);
                    break;
                case "p":
                    e = this.renderPerformance(t);
                    break;
                case "t":
                    e = this.renderTarget(t)
                }
                this.valueShapes[i] = e.id,
                this.shapes[e.id] = i,
                this.target.replaceWithShape(s, e)
            },
            renderRange: function(t, e) {
                var i = this.values[t]
                  , i = L.round(this.canvasWidth * ((i - this.min) / this.range))
                  , t = this.options.get("rangeColors")[t - 2];
                return e && (t = this.calcHighlightColor(t, this.options)),
                this.target.drawRect(0, 0, i - 1, this.canvasHeight - 1, t, t)
            },
            renderPerformance: function(t) {
                var e = this.values[1]
                  , i = L.round(this.canvasWidth * ((e - this.min) / this.range))
                  , e = this.options.get("performanceColor");
                return t && (e = this.calcHighlightColor(e, this.options)),
                this.target.drawRect(0, L.round(.3 * this.canvasHeight), i - 1, L.round(.4 * this.canvasHeight) - 1, e, e)
            },
            renderTarget: function(t) {
                var e = this.values[0]
                  , i = L.round(this.canvasWidth * ((e - this.min) / this.range) - this.options.get("targetWidth") / 2)
                  , s = L.round(.1 * this.canvasHeight)
                  , n = this.canvasHeight - 2 * s
                  , e = this.options.get("targetColor");
                return t && (e = this.calcHighlightColor(e, this.options)),
                this.target.drawRect(i, s, this.options.get("targetWidth") - 1, n - 1, e, e)
            },
            render: function() {
                var t, e, i = this.values.length, s = this.target;
                if (p._super.render.call(this)) {
                    for (t = 2; t < i; t++)
                        e = this.renderRange(t).append(),
                        this.shapes[e.id] = "r" + t,
                        this.valueShapes["r" + t] = e.id;
                    null !== this.values[1] && (e = this.renderPerformance().append(),
                    this.shapes[e.id] = "p1",
                    this.valueShapes.p1 = e.id),
                    null !== this.values[0] && (e = this.renderTarget().append(),
                    this.shapes[e.id] = "t0",
                    this.valueShapes.t0 = e.id),
                    s.render()
                }
            }
        }),
        H.fn.sparkline.pie = u = x(H.fn.sparkline._base, {
            type: "pie",
            init: function(t, e, i, s, n) {
                var r, a = 0;
                if (u._super.init.call(this, t, e, i, s, n),
                this.shapes = {},
                this.valueShapes = {},
                this.values = e = H.map(e, Number),
                "auto" === i.get("width") && (this.width = this.height),
                0 < e.length)
                    for (r = e.length; r--; )
                        a += e[r];
                this.total = a,
                this.initTarget(),
                this.radius = L.floor(L.min(this.canvasWidth, this.canvasHeight) / 2)
            },
            getRegion: function(t, e, i) {
                i = this.target.getShapeAt(t, e, i);
                return i !== E && this.shapes[i] !== E ? this.shapes[i] : E
            },
            getCurrentRegionFields: function() {
                var t = this.currentRegion;
                return {
                    isNull: this.values[t] === E,
                    value: this.values[t],
                    percent: this.values[t] / this.total * 100,
                    color: this.options.get("sliceColors")[t % this.options.get("sliceColors").length],
                    offset: t
                }
            },
            changeHighlight: function(t) {
                var e = this.currentRegion
                  , i = this.renderSlice(e, t)
                  , t = this.valueShapes[e];
                delete this.shapes[t],
                this.target.replaceWithShape(t, i),
                this.valueShapes[e] = i.id,
                this.shapes[i.id] = e
            },
            renderSlice: function(t, e) {
                for (var i, s, n, r = this.target, a = this.options, o = this.radius, h = a.get("borderWidth"), l = a.get("offset"), g = 2 * L.PI, p = this.values, u = this.total, c = l ? 2 * L.PI * (l / 360) : 0, d = p.length, f = 0; f < d; f++) {
                    if (s = i = c,
                    0 < u && (s = c + g * (p[f] / u)),
                    t === f)
                        return n = a.get("sliceColors")[f % a.get("sliceColors").length],
                        e && (n = this.calcHighlightColor(n, a)),
                        r.drawPieSlice(o, o, o - h, i, s, E, n);
                    c = s
                }
            },
            render: function() {
                var t, e, i = this.target, s = this.values, n = this.options, r = this.radius, a = n.get("borderWidth"), o = n.get("donutWidth");
                if (u._super.render.call(this)) {
                    for (a && i.drawCircle(r, r, L.floor(r - a / 2), n.get("borderColor"), E, a).append(),
                    e = s.length; e--; )
                        s[e] && (t = this.renderSlice(e).append(),
                        this.valueShapes[e] = t.id,
                        this.shapes[t.id] = e);
                    o && i.drawCircle(r, r, r - o, n.get("donutColor"), n.get("donutColor"), 0).append(),
                    i.render()
                }
            }
        }),
        H.fn.sparkline.box = C = x(H.fn.sparkline._base, {
            type: "box",
            init: function(t, e, i, s, n) {
                C._super.init.call(this, t, e, i, s, n),
                this.values = H.map(e, Number),
                this.width = "auto" === i.get("width") ? "4.0em" : s,
                this.initTarget(),
                this.values.length || (this.disabled = 1)
            },
            getRegion: function() {
                return 1
            },
            getCurrentRegionFields: function() {
                var t = [{
                    field: "lq",
                    value: this.quartiles[0]
                }, {
                    field: "med",
                    value: this.quartiles[1]
                }, {
                    field: "uq",
                    value: this.quartiles[2]
                }];
                return this.loutlier !== E && t.push({
                    field: "lo",
                    value: this.loutlier
                }),
                this.routlier !== E && t.push({
                    field: "ro",
                    value: this.routlier
                }),
                this.lwhisker !== E && t.push({
                    field: "lw",
                    value: this.lwhisker
                }),
                this.rwhisker !== E && t.push({
                    field: "rw",
                    value: this.rwhisker
                }),
                t
            },
            render: function() {
                var t, e, i, s, n, r, a, o, h, l, g = this.target, p = this.values, u = p.length, c = this.options, d = this.canvasWidth, f = this.canvasHeight, m = c.get("chartRangeMin") === E ? L.min.apply(L, p) : c.get("chartRangeMin"), v = c.get("chartRangeMax") === E ? L.max.apply(L, p) : c.get("chartRangeMax"), x = 0;
                if (C._super.render.call(this)) {
                    if (c.get("raw"))
                        c.get("showOutliers") && 5 < p.length ? (e = p[0],
                        t = p[1],
                        s = p[2],
                        h = p[3],
                        n = p[4],
                        r = p[5],
                        a = p[6]) : (t = p[0],
                        s = p[1],
                        h = p[2],
                        n = p[3],
                        r = p[4]);
                    else if (p.sort(function(t, e) {
                        return t - e
                    }),
                    s = y(p, 1),
                    h = y(p, 2),
                    i = (n = y(p, 3)) - s,
                    c.get("showOutliers")) {
                        for (t = r = E,
                        o = 0; o < u; o++)
                            t === E && p[o] > s - i * c.get("outlierIQR") && (t = p[o]),
                            p[o] < n + i * c.get("outlierIQR") && (r = p[o]);
                        e = p[0],
                        a = p[u - 1]
                    } else
                        t = p[0],
                        r = p[u - 1];
                    this.quartiles = [s, h, n],
                    this.lwhisker = t,
                    this.rwhisker = r,
                    this.loutlier = e,
                    this.routlier = a,
                    l = d / (v - m + 1),
                    c.get("showOutliers") && (x = L.ceil(c.get("spotRadius")),
                    l = (d -= 2 * L.ceil(c.get("spotRadius"))) / (v - m + 1),
                    e < t && g.drawCircle((e - m) * l + x, f / 2, c.get("spotRadius"), c.get("outlierLineColor"), c.get("outlierFillColor")).append(),
                    r < a && g.drawCircle((a - m) * l + x, f / 2, c.get("spotRadius"), c.get("outlierLineColor"), c.get("outlierFillColor")).append()),
                    g.drawRect(L.round((s - m) * l + x), L.round(.1 * f), L.round((n - s) * l), L.round(.8 * f), c.get("boxLineColor"), c.get("boxFillColor")).append(),
                    g.drawLine(L.round((t - m) * l + x), L.round(f / 2), L.round((s - m) * l + x), L.round(f / 2), c.get("lineColor")).append(),
                    g.drawLine(L.round((t - m) * l + x), L.round(f / 4), L.round((t - m) * l + x), L.round(f - f / 4), c.get("whiskerColor")).append(),
                    g.drawLine(L.round((r - m) * l + x), L.round(f / 2), L.round((n - m) * l + x), L.round(f / 2), c.get("lineColor")).append(),
                    g.drawLine(L.round((r - m) * l + x), L.round(f / 4), L.round((r - m) * l + x), L.round(f - f / 4), c.get("whiskerColor")).append(),
                    g.drawLine(L.round((h - m) * l + x), L.round(.1 * f), L.round((h - m) * l + x), L.round(.9 * f), c.get("medianColor")).append(),
                    c.get("target") && (h = L.ceil(c.get("spotRadius")),
                    g.drawLine(L.round((c.get("target") - m) * l + x), L.round(f / 2 - h), L.round((c.get("target") - m) * l + x), L.round(f / 2 + h), c.get("targetColor")).append(),
                    g.drawLine(L.round((c.get("target") - m) * l + x - h), L.round(f / 2), L.round((c.get("target") - m) * l + x + h), L.round(f / 2), c.get("targetColor")).append()),
                    g.render()
                }
            }
        }),
        s = x({
            init: function(t, e, i, s) {
                this.target = t,
                this.id = e,
                this.type = i,
                this.args = s
            },
            append: function() {
                return this.target.appendShape(this),
                this
            }
        }),
        i = x({
            _pxregex: /(\d+)(px)?\s*$/i,
            init: function(t, e, i) {
                t && (this.width = t,
                this.height = e,
                this.target = i,
                this.lastShapeId = null,
                i[0] && (i = i[0]),
                H.data(i, "_jqs_vcanvas", this))
            },
            drawLine: function(t, e, i, s, n, r) {
                return this.drawShape([[t, e], [i, s]], n, r)
            },
            drawShape: function(t, e, i, s) {
                return this._genShape("Shape", [t, e, i, s])
            },
            drawCircle: function(t, e, i, s, n, r) {
                return this._genShape("Circle", [t, e, i, s, n, r])
            },
            drawPieSlice: function(t, e, i, s, n, r, a) {
                return this._genShape("PieSlice", [t, e, i, s, n, r, a])
            },
            drawRect: function(t, e, i, s, n, r) {
                return this._genShape("Rect", [t, e, i, s, n, r])
            },
            getElement: function() {
                return this.canvas
            },
            getLastShapeId: function() {
                return this.lastShapeId
            },
            reset: function() {
                alert("reset not implemented")
            },
            _insert: function(t, e) {
                H(e).html(t)
            },
            _calculatePixelDims: function(t, e, i) {
                e = this._pxregex.exec(e);
                this.pixelHeight = e ? e[1] : H(i).height(),
                e = this._pxregex.exec(t),
                this.pixelWidth = e ? e[1] : H(i).width()
            },
            _genShape: function(t, e) {
                var i = m++;
                return e.unshift(i),
                new s(this,i,t,e)
            },
            appendShape: function(t) {
                alert("appendShape not implemented")
            },
            replaceWithShape: function(t, e) {
                alert("replaceWithShape not implemented")
            },
            insertAfterShape: function(t, e) {
                alert("insertAfterShape not implemented")
            },
            removeShapeId: function(t) {
                alert("removeShapeId not implemented")
            },
            getShapeAt: function(t, e, i) {
                alert("getShapeAt not implemented")
            },
            render: function() {
                alert("render not implemented")
            }
        }),
        c = x(i, {
            init: function(t, e, i, s) {
                c._super.init.call(this, t, e, i),
                this.canvas = _.createElement("canvas"),
                i[0] && (i = i[0]),
                H.data(i, "_jqs_vcanvas", this),
                H(this.canvas).css({
                    display: "inline-block",
                    width: t,
                    height: e,
                    verticalAlign: "top"
                }),
                this._insert(this.canvas, i),
                this._calculatePixelDims(t, e, this.canvas),
                this.canvas.width = this.pixelWidth,
                this.canvas.height = this.pixelHeight,
                this.interact = s,
                this.shapes = {},
                this.shapeseq = [],
                this.currentTargetShapeId = E,
                H(this.canvas).css({
                    width: this.pixelWidth,
                    height: this.pixelHeight
                })
            },
            _getContext: function(t, e, i) {
                var s = this.canvas.getContext("2d");
                return t !== E && (s.strokeStyle = t),
                s.lineWidth = i === E ? 1 : i,
                e !== E && (s.fillStyle = e),
                s
            },
            reset: function() {
                this._getContext().clearRect(0, 0, this.pixelWidth, this.pixelHeight),
                this.shapes = {},
                this.shapeseq = [],
                this.currentTargetShapeId = E
            },
            _drawShape: function(t, e, i, s, n) {
                var r, a, o = this._getContext(i, s, n);
                for (o.beginPath(),
                o.moveTo(e[0][0] + .5, e[0][1] + .5),
                r = 1,
                a = e.length; r < a; r++)
                    o.lineTo(e[r][0] + .5, e[r][1] + .5);
                i !== E && o.stroke(),
                s !== E && o.fill(),
                this.targetX !== E && this.targetY !== E && o.isPointInPath(this.targetX, this.targetY) && (this.currentTargetShapeId = t)
            },
            _drawCircle: function(t, e, i, s, n, r, a) {
                a = this._getContext(n, r, a);
                a.beginPath(),
                a.arc(e, i, s, 0, 2 * L.PI, !1),
                this.targetX !== E && this.targetY !== E && a.isPointInPath(this.targetX, this.targetY) && (this.currentTargetShapeId = t),
                n !== E && a.stroke(),
                r !== E && a.fill()
            },
            _drawPieSlice: function(t, e, i, s, n, r, a, o) {
                var h = this._getContext(a, o);
                h.beginPath(),
                h.moveTo(e, i),
                h.arc(e, i, s, n, r, !1),
                h.lineTo(e, i),
                h.closePath(),
                a !== E && h.stroke(),
                o && h.fill(),
                this.targetX !== E && this.targetY !== E && h.isPointInPath(this.targetX, this.targetY) && (this.currentTargetShapeId = t)
            },
            _drawRect: function(t, e, i, s, n, r, a) {
                return this._drawShape(t, [[e, i], [e + s, i], [e + s, i + n], [e, i + n], [e, i]], r, a)
            },
            appendShape: function(t) {
                return this.shapes[t.id] = t,
                this.shapeseq.push(t.id),
                this.lastShapeId = t.id,
                t.id
            },
            replaceWithShape: function(t, e) {
                var i, s = this.shapeseq;
                for (this.shapes[e.id] = e,
                i = s.length; i--; )
                    s[i] == t && (s[i] = e.id);
                delete this.shapes[t]
            },
            replaceWithShapes: function(t, e) {
                for (var i, s, n = this.shapeseq, r = {}, a = t.length; a--; )
                    r[t[a]] = !0;
                for (a = n.length; a--; )
                    r[i = n[a]] && (n.splice(a, 1),
                    delete this.shapes[i],
                    s = a);
                for (a = e.length; a--; )
                    n.splice(s, 0, e[a].id),
                    this.shapes[e[a].id] = e[a]
            },
            insertAfterShape: function(t, e) {
                for (var i = this.shapeseq, s = i.length; s--; )
                    if (i[s] === t)
                        return i.splice(s + 1, 0, e.id),
                        void (this.shapes[e.id] = e)
            },
            removeShapeId: function(t) {
                for (var e = this.shapeseq, i = e.length; i--; )
                    if (e[i] === t) {
                        e.splice(i, 1);
                        break
                    }
                delete this.shapes[t]
            },
            getShapeAt: function(t, e, i) {
                return this.targetX = e,
                this.targetY = i,
                this.render(),
                this.currentTargetShapeId
            },
            render: function() {
                var t, e, i = this.shapeseq, s = this.shapes, n = i.length;
                for (this._getContext().clearRect(0, 0, this.pixelWidth, this.pixelHeight),
                e = 0; e < n; e++)
                    this["_draw" + (t = s[i[e]]).type].apply(this, t.args);
                this.interact || (this.shapes = {},
                this.shapeseq = [])
            }
        }),
        d = x(i, {
            init: function(t, e, i) {
                d._super.init.call(this, t, e, i),
                i[0] && (i = i[0]),
                H.data(i, "_jqs_vcanvas", this),
                this.canvas = _.createElement("span"),
                H(this.canvas).css({
                    display: "inline-block",
                    position: "relative",
                    overflow: "hidden",
                    width: t,
                    height: e,
                    margin: "0px",
                    padding: "0px",
                    verticalAlign: "top"
                }),
                this._insert(this.canvas, i),
                this._calculatePixelDims(t, e, this.canvas),
                this.canvas.width = this.pixelWidth,
                this.canvas.height = this.pixelHeight,
                e = '<v:group coordorigin="0 0" coordsize="' + this.pixelWidth + " " + this.pixelHeight + '" style="position:absolute;top:0;left:0;width:' + this.pixelWidth + "px;height=" + this.pixelHeight + 'px;"></v:group>',
                this.canvas.insertAdjacentHTML("beforeEnd", e),
                this.group = H(this.canvas).children()[0],
                this.rendered = !1,
                this.prerender = ""
            },
            _drawShape: function(t, e, i, s, n) {
                for (var r, a, o = [], h = 0, l = e.length; h < l; h++)
                    o[h] = e[h][0] + "," + e[h][1];
                return r = o.splice(0, 1),
                n = n === E ? 1 : n,
                a = o[0] === o[o.length - 1] ? "x " : "",
                '<v:shape coordorigin="0 0" coordsize="' + this.pixelWidth + " " + this.pixelHeight + '"  id="jqsshape' + t + '" ' + (i === E ? ' stroked="false" ' : ' strokeWeight="' + n + 'px" strokeColor="' + i + '" ') + (s === E ? ' filled="false"' : ' fillColor="' + s + '" filled="true" ') + ' style="position:absolute;left:0px;top:0px;height:' + this.pixelHeight + "px;width:" + this.pixelWidth + 'px;padding:0px;margin:0px;"  path="m ' + r + " l " + o.join(", ") + " " + a + 'e"> </v:shape>'
            },
            _drawCircle: function(t, e, i, s, n, r, a) {
                return '<v:oval  id="jqsshape' + t + '" ' + (n === E ? ' stroked="false" ' : ' strokeWeight="' + a + 'px" strokeColor="' + n + '" ') + (r === E ? ' filled="false"' : ' fillColor="' + r + '" filled="true" ') + ' style="position:absolute;top:' + (i -= s) + "px; left:" + (e -= s) + "px; width:" + 2 * s + "px; height:" + 2 * s + 'px"></v:oval>'
            },
            _drawPieSlice: function(t, e, i, s, n, r, a, o) {
                var h, l, g, p;
                if (n === r)
                    return "";
                if (r - n == 2 * L.PI && (n = 0,
                r = 2 * L.PI),
                h = e + L.round(L.cos(n) * s),
                l = i + L.round(L.sin(n) * s),
                g = e + L.round(L.cos(r) * s),
                p = i + L.round(L.sin(r) * s),
                h === g && l === p) {
                    if (r - n < L.PI)
                        return "";
                    h = g = e + s,
                    l = p = i
                }
                return h === g && l === p && r - n < L.PI ? "" : '<v:shape coordorigin="0 0" coordsize="' + this.pixelWidth + " " + this.pixelHeight + '"  id="jqsshape' + t + '" ' + (a === E ? ' stroked="false" ' : ' strokeWeight="1px" strokeColor="' + a + '" ') + (o === E ? ' filled="false"' : ' fillColor="' + o + '" filled="true" ') + ' style="position:absolute;left:0px;top:0px;height:' + this.pixelHeight + "px;width:" + this.pixelWidth + 'px;padding:0px;margin:0px;"  path="m ' + e + "," + i + " wa " + [e - s, i - s, e + s, i + s, h, l, g, p].join(", ") + ' x e"> </v:shape>'
            },
            _drawRect: function(t, e, i, s, n, r, a) {
                return this._drawShape(t, [[e, i], [e, i + n], [e + s, i + n], [e + s, i], [e, i]], r, a)
            },
            reset: function() {
                this.group.innerHTML = ""
            },
            appendShape: function(t) {
                var e = this["_draw" + t.type].apply(this, t.args);
                return this.rendered ? this.group.insertAdjacentHTML("beforeEnd", e) : this.prerender += e,
                this.lastShapeId = t.id,
                t.id
            },
            replaceWithShape: function(t, e) {
                t = H("#jqsshape" + t),
                e = this["_draw" + e.type].apply(this, e.args);
                t[0].outerHTML = e
            },
            replaceWithShapes: function(t, e) {
                for (var i = H("#jqsshape" + t[0]), s = "", n = e.length, r = 0; r < n; r++)
                    s += this["_draw" + e[r].type].apply(this, e[r].args);
                for (i[0].outerHTML = s,
                r = 1; r < t.length; r++)
                    H("#jqsshape" + t[r]).remove()
            },
            insertAfterShape: function(t, e) {
                t = H("#jqsshape" + t),
                e = this["_draw" + e.type].apply(this, e.args);
                t[0].insertAdjacentHTML("afterEnd", e)
            },
            removeShapeId: function(t) {
                t = H("#jqsshape" + t);
                this.group.removeChild(t[0])
            },
            getShapeAt: function(t, e, i) {
                return t.id.substr(8)
            },
            render: function() {
                this.rendered || (this.group.innerHTML = this.prerender,
                this.rendered = !0)
            }
        })
    }
    ,
    "function" == typeof define && define.amd ? define(["jquery"], t) : jQuery && !jQuery.fn.sparkline && t(jQuery)
}(document, Math);
