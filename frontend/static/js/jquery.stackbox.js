/*
   --------------------------------
   Stackbox.js
   --------------------------------
   + https://github.com/stebru/stackbox
   + version 0.3.4
   + Copyright 2014-2015 Stefan Bruvik
   + Licensed under the MIT license

   + Documentation: http://stefan.codes/stackbox
 */

/* global jQuery */
(function stackbox($, window) {

  'use strict';

  var stackboxCounter = 0,
    stackboxGroup = 0,
    stackboxes = [],
    domElements = [],
    minMarginLeft = 20,
    minMarginRight = 34,
    minMarginTop = 10,
    defaultStackboxClass = 'stackbox',
    defaultWrapperClass = 'stackbox-wrapper',
    css3animsupported = false,
    animationEventNames = 'animationend webkitAnimationEnd MSAnimationEnd oAnimationEnd';

  function returnFunction(fn) {

    var ns;

    if (typeof fn === 'string') {

      if ($.fn.stackbox.globalSettings && typeof $.fn.stackbox.globalSettings.NAMESPACE === 'string') {

        ns = $.fn.stackbox.globalSettings.NAMESPACE;

        if (window[ns] && $.isFunction(window[ns][fn])) {
          return window[ns][fn];
        }
      }

      if ($.isFunction(window[fn])) {
        return window[fn];
      }
    }

    if ($.isFunction(fn)) {
      return fn;
    }

    return function notFound() {
      console.warn('Function not found', fn);
    };
  }

  function openTrigger(event) {

    /*jshint validthis:true */

    event.preventDefault();
    $(this).addClass('active').stackbox();
  }

  function escapeKeyClick(event) {
    if (event.keyCode === 27) {
      closeTopmostStackbox();
      event.preventDefault();
    }
  }

  function closeTopmostStackbox() {
    var stackboxObj = stackboxes[stackboxes.length - 1];
    if (stackboxObj) {
      stackboxObj.exitStackbox(true);
    }
  }

  function closeStackboxContainingElement($element) {

    var $targetStackbox = $element.parents('.stackbox'),
      targetIndex,
      stackboxObj,
      i;

    if ($targetStackbox.length) {

      targetIndex = $targetStackbox.data('stackboxIndex');

      for (i = stackboxes.length - 1; i >= 0; i--) {
        if (i >= targetIndex) {
          stackboxObj = stackboxes[i];
          if (stackboxObj) {
            stackboxObj.exitStackbox(true);
          }
        }
      }
    }
  }

  function stackboxMousedown(event) {

    var element = event.target,
      $element = $(element),
      stackboxObj,
      targetIndex,
      targetGroup,
      currentGroup,
      i,
      clickedVScrollBar,
      clickedHScrollBar,
      $window = $(window),
      closeThese = [],
      stackboxClass = defaultStackboxClass,
      wrapperClass = defaultWrapperClass;

    if (event.which !== 1) {
      return false;
    }

    if ($.fn.stackbox.globalSettings && $.fn.stackbox.globalSettings.stackboxclass) {
      stackboxClass = $.fn.stackbox.globalSettings.stackboxclass;
    }
    if ($.fn.stackbox.globalSettings && $.fn.stackbox.globalSettings.wrapperclass) {
      wrapperClass = $.fn.stackbox.globalSettings.wrapperclass;
    }

    while (element && element !== document.body && element !== document) {
      $element = $(element);

      if ($element.data('closeStackbox') === true) { // Click on close-stackbox=true is handled in stackbox#closeClick
        return false;
      }

      if ($element.hasClass(stackboxClass)) { // Clicked inside of stackbox, close all stackboxes stacked on top of this one.
        targetIndex = $element.data('stackboxIndex');

        for (i = stackboxes.length - 1; i >= 0; i--) {
          if (i > targetIndex) {
            stackboxObj = stackboxes[i];
            if (stackboxObj) {
              stackboxObj.exitStackbox(true);
            }
          }
        }

        return true; // Let event bubble up

      } else {
        element = element.parentNode;
      }
    }

    // Detect mousedown on scrollbars
    $element = $(event.target);

    clickedVScrollBar = (($window.outerWidth() - event.clientX) < ($element[0].offsetWidth - $element[0].clientWidth));
    clickedHScrollBar = (($window.outerHeight() - event.clientY) < ($element[0].offsetHeight - $element[0].clientHeight));

    if (clickedVScrollBar || clickedHScrollBar) {
      return false;
    }

    if (stackboxes.length === 1) {
      // Clicked somewhere in the document (through wrapper)
      stackboxObj = stackboxes[0];
      if (stackboxObj) {
        if (stackboxObj.$wrapper[0].style.pointerEvents === 'none') {
          // Only one stackbox (with offspring) open. Close it.
          stackboxObj.exitStackbox(true);
          return true; // Let event bubble up
        }
      }
    }

    if ($.fn.stackbox.globalSettings && $.fn.stackbox.globalSettings.whitelist) {
      for (i = 0; i < $.fn.stackbox.globalSettings.whitelist.length; i++) {
        if ($element.parents('.' + $.fn.stackbox.globalSettings.whitelist[i]).length) {
          return true;
        }
      }
    }

    // Clicked outside of stackbox, i.e. on wrapper.
    targetGroup = $element.data('stackboxGroup');
    if (targetGroup) {
      for (i = stackboxes.length - 1; i >= 0; i--) {
        stackboxObj = stackboxes[i];
        if (stackboxObj) {
          currentGroup = stackboxObj.$stackbox.data('stackboxGroup');
          if (currentGroup === targetGroup) {
            closeThese.push(stackboxObj);
          }
        }
      }

      if (closeThese.length) {
        if (closeThese.length === 1 && closeThese[0].options.closeOnBackdrop === true) {
          // Last one in group, close it.
          closeThese[0].exitStackbox(true);
        } else {
          // Close all but the lowest stackbox in group.
          for (i = 0; i < closeThese.length - 1; i++) {
            if (closeThese[i].options.closeOnBackdrop === true) {
              closeThese[i].exitStackbox(true);
            }
          }
        }
      }
    } else {
      // All stackboxes are 'drop downs' (i.e. none of them have backdrop), contained in a single wrapper. Close them all.
      for (i = stackboxes.length - 1; i >= 0; i--) {
        stackboxObj = stackboxes[i];
        if (stackboxObj) {
          stackboxObj.exitStackbox(true);
        }
      }
    }
  }

  function windowResize() {

    var stackboxObj,
      i;

    for (i = 0; i < stackboxCounter; i++) {
      stackboxObj = stackboxes[i];
      if (stackboxObj) {
        stackboxObj.updatePosition(stackboxObj);
      }
    }
  }

  function windowScroll() {
    windowResize();
  }

  var stackboxPrototype = {

    init: function(options, parentElement) {

      var href,
        animDone;

      this.options = $.extend({}, $.fn.stackbox.settings, options, $.fn.stackbox.globalSettings);

      this.previousDimensions = {
        width: 0,
        height: 0
      };

      if (this.options.position === 'fixed') {
        this.options.position = 'absolute';
      }

      this.loadable = false;

      if (this.options.nextTo !== null) {
        this.$offspring = $(this.options.nextTo);
      } else {
        if (parentElement !== undefined) {
          this.$offspring = $(parentElement);
        } else {
          this.options.position = 'absolute';
        }
      }

      if (this.options.backdrop === 'auto') {
        if (this.options.position === 'absolute') {
          this.options.backdrop = true;
        } else {
          this.options.backdrop = false;
        }
      }

      this.createDOMElements();

      href = $(parentElement).attr('href');
      if (this.options.content === false && href) {
        this.options.content = href;
      }

      this.addContent();

      if (this.loadable !== true) { // If loadable, created in loadAjax()
        this.createCloseButton();
      }

      this.createArrow();

      this.addEventListeners();

      this.created = true;

      returnFunction(this.options.beforeOpen)(this.$offspring, this);
      $(document).trigger('beforeOpen.stackbox', [this.$offspring, this]);

      if (this.loadable === true) {
        this.loadAjax(this.options.content);
      } else {

        this.updatePosition();

        animDone = function animDone() {
          this.$stackbox.removeClass('animated ' + this.options.animOpen);
          this.afterOpen(true);
        }.bind(this);

        if (css3animsupported) {
          this.$stackbox.addClass('animated ' + this.options.animOpen).off(animationEventNames).on(animationEventNames, animDone);
        } else {
          animDone();
        }
      }
    },

    afterOpen: function(updatePosition) {

      if (updatePosition === true) {
        this.updatePosition();
      }

      this.autoScroll();

      returnFunction(this.options.afterOpen)(this.$stackbox, this.$offspring, this);
      $(document).trigger('afterOpen.stackbox', [this.$stackbox, this.$offspring, this]);
    },

    createArrow: function() {

      if (this.$offspring === undefined || this.options.position === 'absolute') {
        this.$arrow = false;
        return;
      }

      $('<div class="stackbox-arrow"></div>').appendTo(this.$stackbox);
      this.$arrow = this.$stackbox.find('.stackbox-arrow');
      this.arrowWidth = this.$arrow.outerWidth();
      this.arrowHeight = this.$arrow.outerHeight();
    },

    createCloseButton: function() {

      var closeButtonIcon;

      if (this.options.closeButton === true) {

        if ($.fn.stackbox.globalSettings && $.fn.stackbox.globalSettings.closeButtonIcon) {
          closeButtonIcon = $.fn.stackbox.globalSettings.closeButtonIcon;
        } else {
          closeButtonIcon = this.options.closeButtonIcon;
        }

        this.$closeButton = $('<div class="stackbox-close" data-close-stackbox="true"><button type="button" class="close">' + closeButtonIcon + '</button></div>');
        this.$stackbox.prepend(this.$closeButton);
      }
    },

    createDOMElements: function() {

      var $parent,
        stackboxIndex,
        newStackboxGroup,
        stackboxCss = {
          display: 'block'
        },
        wrapperClass = defaultWrapperClass,
        stackboxClass = defaultStackboxClass,
        mainWrapperClass = this.options.mainWrapperClass,
        mainWrapperExtraClass = '';

      if ($.fn.stackbox.globalSettings && $.fn.stackbox.globalSettings.stackboxclass) {
        stackboxClass = $.fn.stackbox.globalSettings.stackboxclass;
      }

      if (this.$offspring) {
        $parent = this.$offspring.parents('.' + stackboxClass);
      }

      if ($.fn.stackbox.globalSettings && $.fn.stackbox.globalSettings.mainWrapperClass) {
        mainWrapperClass = $.fn.stackbox.globalSettings.mainWrapperClass;
        if ($.fn.stackbox.globalSettings.mainwrapperextraclass) {
          mainWrapperExtraClass += ' ' + $.fn.stackbox.globalSettings.mainwrapperextraclass;
        }
      }

      if (stackboxCounter === 1) {
        this.$wrapperWrapper = $('<div></div>').addClass(mainWrapperClass + mainWrapperExtraClass).appendTo($(document.body));
      } else if ($parent) {
        this.$wrapperWrapper = $parent.parents('.' + mainWrapperClass);
      }

      if (stackboxCounter === 1 || this.options.backdrop === true) {

        this.$wrapper = $('<div></div>')
          .addClass(wrapperClass)
          .css('z-index', 9900 + stackboxCounter)
          .appendTo(this.$wrapperWrapper);

        if (stackboxCounter === 1 && this.options.backdrop !== true) {
          this.$wrapper.css({
            'overflow': 'hidden',
            'pointer-events': 'none'
          });
        }

        stackboxGroup++;
        this.$wrapper.data('stackboxGroup', stackboxGroup);
        $(document).off('mousedown.stackbox').on('mousedown.stackbox', stackboxMousedown);

      } else if ($parent) {
        this.$wrapper = $parent.parent();
      }

      this.hadNoScroll = $('html').hasClass(this.options.noscrollClass);

      if (this.options.backdrop === true) {
        this.$wrapper.addClass('stackbox-backdrop');
      }

      if (this.options.position === 'absolute') {
        $('html').addClass(this.options.noscrollClass);
      }

      if (this.options.width === 'auto') {
        stackboxCss.width = 'auto';
      }

      // Create the stackbox element.
      this.$stackbox = $('<div></div>')
        .addClass(stackboxClass)
        .css(stackboxCss)
        .appendTo(this.$wrapper);

      if (this.options.closeOnBackdrop === true) {
        this.$wrapper.addClass('stackbox-close-on-backdrop');
      } else {
        this.$wrapper.removeClass('stackbox-close-on-backdrop');
      }

      stackboxIndex = (stackboxCounter - 1);
      this.stackboxIndex = stackboxIndex;
      this.$stackbox.data('stackboxIndex', stackboxIndex);

      newStackboxGroup = this.$wrapper.data('stackboxGroup');
      this.stackboxGroup = newStackboxGroup;
      this.$stackbox.data('stackboxGroup', newStackboxGroup);
    },

    addEventListeners: function() {

      if (this.options.autoadjust === true) {
        var checkDimensions = function check() {

          if (this.$stackbox.outerWidth() !== this.previousDimensions.width || this.$stackbox.outerHeight() !== this.previousDimensions.height) {
            this.updatePosition();
          }

          this.timeoutID = window.setTimeout(checkDimensions, 250);
        }.bind(this);

        checkDimensions();
      }

      this.$stackbox.on('click', '[data-close-stackbox="true"]', {
        stackbox: this.$stackbox
      }, this.closeClick);
    },

    closeClick: function(event) {
      var stackboxObj,
        $stackbox = event.data.stackbox,
        targetIndex = $stackbox.data('stackboxIndex'),
        i,
        $this = $(this);

      event.preventDefault();
      event.stopPropagation(); // Stop event from bubbling up to document click listener (handled by openTrigger).

      for (i = stackboxCounter - 1; i >= 0; i--) {
        if (i >= targetIndex) {
          stackboxObj = stackboxes[i];
          if (stackboxObj) {
            if ($this.data('stackbox') === true) {
              stackboxObj.exitStackbox(false, function onClosed() {
                $this.stackbox();
              });
            } else {
              stackboxObj.exitStackbox();
            }
          }
        }
      }
    },

    loadAjax: function(options) {

      var ajaxDone,
        ajaxFail,
        ajaxAlways,
        animDone,
        spinnerClass;

      if (typeof options === 'string') {
        options = {
          url: options,
          dataType: 'html',
          type: this.options.requestType
        };
      }

      // Display the loading spinner as stackbox content.
      if (this.$arrow) {
        this.$arrow = this.$stackbox.find('.stackbox-arrow').detach();
      }

      if ($.fn.stackbox.globalSettings && $.fn.stackbox.globalSettings.spinnerClass) {
        spinnerClass = $.fn.stackbox.globalSettings.spinnerClass;
      } else {
        spinnerClass = this.options.spinnerClass;
      }

      this.$stackbox.html('<div style="padding: 40px; text-align: center;"><div class="' + spinnerClass + '"></div></div>');

      if (this.$arrow) {
        this.$arrow.appendTo(this.$stackbox);
      }

      this.updatePosition();

      if (this.options.queryParams !== null) {
        if (typeof this.options.queryParams === 'string') {
          options.data = $.parseJSON(this.options.queryParams.replace(/'/g, '"'));
        } else if (typeof this.options.queryParams === 'object') {
          options.data = this.options.queryParams;
        }
      }

      if (this.$arrow) {
        this.setArrowPos();
      }

      this.ajaxRequest = $.ajax(options);

      ajaxDone = function ajaxDone(data) {

        this.$stackbox.hide();
        this.$stackbox.html(data);

        if (this.$arrow) {
          this.$arrow.appendTo(this.$stackbox);
        }
      }.bind(this);

      ajaxFail = function ajaxFail(jqXHR, textStatus) {
        var htmlMessage,
          messengerMessage = this.options.requestFailed;

        if (jqXHR && jqXHR.responseText && jqXHR.responseText.length > 0) {
          htmlMessage = jqXHR.responseText;
        } else {
          htmlMessage = this.options.requestFailed;
        }

        if (options && options.url) {
          messengerMessage += ' Url: ' + options.url;
        }

        if (textStatus !== 'abort') {
          console.warn(messengerMessage);
          returnFunction(this.options.onError)(this, jqXHR, textStatus);
          this.$stackbox.trigger('onError.stackbox', [this, jqXHR, textStatus]);
        }

        this.$stackbox.html('<div style="padding: 10px;">' + htmlMessage + '</div>');
      }.bind(this);

      ajaxAlways = function ajaxAlways() {

        this.createCloseButton();

        // <- Don't ask...
        this.updatePosition(); // 1
        this.updatePosition(); // 2
        // ->

        animDone = function animDone() {

          this.$stackbox.removeClass('animated ' + this.options.animOpen);
          this.afterOpen();

        }.bind(this);

        if (css3animsupported) {
          this.$stackbox.show(0).addClass('animated ' + this.options.animOpen).off(animationEventNames).on(animationEventNames, animDone);
        } else {
          this.$stackbox.fadeIn(200, function fadeInDone() {
            animDone();
          });
        }

      }.bind(this);

      this.ajaxRequest.fail(ajaxFail);
      this.ajaxRequest.done(ajaxDone);
      this.ajaxRequest.always(ajaxAlways);
    },

    addContent: function() {

      var content = this.options.content,
        $newContent,
        isHttp = (content.match(/^https?:\/\//) || content.charAt(0) === '/');

      if (content.charAt(0) === '#') { // 'content' is a jQuery id, so use it to fetch the real content from the DOM.

        $newContent = $(content);

        if ($newContent.length > 0) {

          $newContent = $newContent.children();

          if (this.options.clone) {
            // Clone an element.
            $newContent.clone(true, true).appendTo(this.$stackbox);
          } else {
            // Don't clone, just extract it from the DOM.
            if (this.options.returnContent) {
              this.returnContent = $($newContent[0]).parent();
            }

            if ($newContent.length === 0) {
              this.$stackbox.html('<div style="padding: 10px;">No content in element: "' + content + '"</div>');
            } else {
              $newContent.appendTo(this.$stackbox);
            }
          }

        } else {
          this.$stackbox.html('<div style="padding: 10px;">Could not find element: "' + content + '"</div>');
        }

      } else if (isHttp) { // Content is an url.

        this.loadable = true;

      } else { // Content is just plain html.

        this.$stackbox.html(content);
      }
    },

    adjustToScroll: function(pos) {

      pos.left -= $(window).scrollLeft();
      pos.left += this.$wrapper.scrollLeft();

      pos.top -= $(window).scrollTop();
      pos.top += this.$wrapper.scrollTop();

      pos.left = Math.round(pos.left);
      pos.top = Math.round(pos.top);

      return pos;
    },

    positionBottom: function(params) {

      var pos = {};

      pos.left = (this.$offspring.offset().left + this.$offspring.outerWidth() / 2) - params.stackboxWidth / 2;
      pos.top = params.marginY + (this.$offspring.offset().top + this.$offspring.outerHeight());

      this.arrowDirection = 'up';

      return this.adjustToScroll(pos);
    },

    positionTop: function(params) {

      var pos = {};

      pos.left = (this.$offspring.offset().left + this.$offspring.outerWidth() / 2) - params.stackboxWidth / 2;
      pos.top = -params.marginY + (this.$offspring.offset().top - params.stackboxHeight);

      this.arrowDirection = 'down';

      return this.adjustToScroll(pos);
    },

    positionLeft: function(params) {

      var pos = {};

      pos.left = this.$offspring.offset().left - params.stackboxWidth - params.marginX;
      pos.top = this.$offspring.offset().top + (this.$offspring.outerHeight() - params.stackboxHeight) / 2;

      this.arrowDirection = 'right';

      return this.adjustToScroll(pos);
    },

    positionRight: function(params) {

      var pos = {};

      pos.left = this.$offspring.offset().left + this.$offspring.outerWidth() + params.marginX;
      pos.top = this.$offspring.offset().top + (this.$offspring.outerHeight() - params.stackboxHeight) / 2;

      this.arrowDirection = 'left';

      return this.adjustToScroll(pos);
    },

    positionAbsolute: function(params) {

      var pos = {},
        $window = $(window);

      pos.left = ($window.width() / 2 - params.stackboxWidth / 2) + $window.scrollLeft();
      pos.top = ($window.outerHeight() / 2 - params.stackboxHeight / 2) + $window.scrollTop();

      this.arrowDirection = false;

      return this.adjustToScroll(pos);
    },

    updatePosition: function() {

      var stackboxWidth,
        stackboxHeight,
        args,
        method,
        css,
        windowWidth = $(window).width();

      if (!this || !this.options) {
        return false;
      }

      if (this.options.width !== 'auto') {
        stackboxWidth = this.calcStackboxWidth();

        if (this.options.respectBrowserWidth) {
          if ((stackboxWidth + minMarginRight) > windowWidth) {
            stackboxWidth = windowWidth - minMarginRight;
          }
        }

        this.$stackbox.width(stackboxWidth);

      } else {
        stackboxWidth = this.$stackbox.width();
      }

      stackboxHeight = this.$stackbox.height();

      args = {
        marginX: this.options.marginX,
        marginY: this.options.marginY,
        stackboxWidth: stackboxWidth,
        stackboxHeight: stackboxHeight
      };

      method = 'position' + this.options.position.charAt(0).toUpperCase() + this.options.position.substring(1);

      // Re-select offspring, in case it was just removed from and re-inserted to the dom.
      if (this.$offspring && this.$offspring.selector) {
        this.$offspring = $(this.$offspring.selector);
      }

      if (!this[method]) {
        console.warn('stackbox: Unknown position method "' + method + '"');
        method = 'positionAbsolute';
      }
      css = this[method](args);
      this.$stackbox.css(css);

      $.extend(args, {
        left: parseInt(this.$stackbox.css('left'), 10),
        top: parseInt(this.$stackbox.css('top'), 10),
        windowWidth: windowWidth,
        windowHeight: $(window).height(),
        width: this.$stackbox.outerWidth(),
        height: this.$stackbox.outerHeight()
      });

      this.adjustToWindow(args);

      if (this.$arrow) {
        this.setArrowPos();
      }
    },

    calcArrowLeft: function() {

      var stackboxLeft = parseInt(this.$stackbox.css('left'), 10),
        stackboxWidth = this.$stackbox.outerWidth(),
        offspringLeft = this.$offspring.offset().left,
        offspringWidth = this.$offspring.outerWidth(),
        offspringCenter = offspringLeft + (offspringWidth / 2),
        arrowWidth = this.arrowWidth,
        halfOfArrow = arrowWidth / 2,
        left,
        minLeft = 6,
        maxLeft = stackboxWidth - arrowWidth - 6;

      left = offspringCenter - stackboxLeft - halfOfArrow; // Subtracting stackboxLeft because arrow's 0,0 is the stackbox's left,top.

      left -= $(window).scrollLeft();
      left += this.$wrapper.scrollLeft();

      if (this.options.position === 'bottom' && this.$closeButton) {
        maxLeft -= (this.$closeButton.outerWidth() - Math.abs(parseInt(this.$closeButton.css('right'), 10)));
      }

      if (left < minLeft) {
        left = minLeft;
      } else if (left > maxLeft) {
        left = maxLeft;
      }

      return left;
    },

    calcArrowTop: function() {

      var stackboxTop = parseInt(this.$stackbox.css('top'), 10),
        stackboxHeight = this.$stackbox.outerHeight(),
        offspringTop = this.$offspring.offset().top,
        offspringHeight = this.$offspring.outerHeight(),
        offspringCenter = offspringTop + (offspringHeight / 2),
        arrowHeight = this.arrowHeight,
        halfOfArrow = arrowHeight / 2,
        top,
        minTop = 6,
        maxTop = stackboxHeight - arrowHeight - 6;

      top = offspringCenter - stackboxTop - halfOfArrow; // Subtracting stackboxTop because arrow's 0,0 is the stackbox's left,top.

      top -= $(window).scrollTop();
      top += this.$wrapper.scrollTop();

      if (top < minTop) {
        top = minTop;
      } else if (top > maxTop) {
        top = maxTop;
      }

      return top;
    },

    setArrowPos: function() {

      var left, top;

      this.$arrow.removeClass('top bottom left right');

      if (this.arrowDirection === 'up') {

        left = this.calcArrowLeft() + (this.arrowWidth / 2);
        top = -(this.arrowHeight / 2);

        this.$arrow.css({
          'left': Math.round(left),
          'top': Math.round(top)
        }).addClass('bottom');

      } else if (this.arrowDirection === 'down') {

        left = this.calcArrowLeft() + (this.arrowWidth / 2);
        top = this.$stackbox.height();

        this.$arrow.css({
          'left': Math.round(left),
          'top': Math.round(top)
        }).addClass('top');

      } else if (this.arrowDirection === 'right') {

        left = this.$stackbox.width();
        top = this.calcArrowTop() + (this.arrowHeight / 2);

        this.$arrow.css({
          'left': Math.round(left),
          'top': Math.round(top)
        }).addClass('left');

      } else if (this.arrowDirection === 'left') {

        left = -(this.arrowWidth - (this.arrowWidth / 2));
        top = this.calcArrowTop() + (this.arrowHeight / 2);

        this.$arrow.css({
          'left': Math.round(left),
          'top': Math.round(top)
        }).addClass('right');
      }
    },

    adjustToWindow: function(params) {

      var left, css;

      if (this.options.autoAdjust === true) { // 自适应.

        if (this.options.position === 'left' || this.options.position === 'right') {

          // Make sure the stackbox is not placed outside of window. If it is, place it below its offspring.
          if (params.top < minMarginTop || params.left < minMarginLeft || params.left + params.width > params.windowWidth - 10) {

            css = this.positionBottom(params); // Position below if not room above.
            this.$stackbox.css(css);
          }
        } else if (this.options.position === 'absolute') {
          if (params.top < minMarginTop) {
            this.$stackbox.css('top', minMarginTop);
          }
        } else {
          if (params.top < minMarginTop) {
            css = this.positionBottom(params); // Position below if not room above.
            this.$stackbox.css(css);
          } else if (params.top + params.height + $(window).scrollTop() > $(document).height()) {
            if (!$('html').hasClass(this.options.noscrollClass)) { // Wrapper can scroll, i.e. there's always room below.
              if (params.top + params.height > $(window).height()) {
                this.$wrapper.css('overflow', 'auto');
                this.$wrapper.css('pointer-events', 'all');
                $('body').css('overflow', 'hidden');
              }
            }
          }
        }
      }

      if (params.left < minMarginLeft) {
        this.$stackbox.css('left', minMarginLeft);
      } else if (params.left + params.stackboxWidth > params.windowWidth - minMarginRight) {
        left = Math.max(minMarginLeft, params.windowWidth - minMarginRight - params.stackboxWidth);
        this.$stackbox.css('left', left);
      }
    },

    calcStackboxWidth: function() {

      var windowWidth = $(window).width(),
        stackboxWidth = this.options.width,
        maxWidth = this.options.maxWidth === false ? 10000 : parseInt(this.options.maxWidth, 10),
        minWidth = this.options.minWidth === false ? 0 : parseInt(this.options.minWidth, 10);

      if (typeof stackboxWidth === 'string') {

        stackboxWidth = parseInt(this.options.width, 10);

        if (this.options.width.indexOf('%') !== -1) {
          stackboxWidth = windowWidth * (stackboxWidth / 100);
        }
      }

      if (stackboxWidth > maxWidth) {
        stackboxWidth = maxWidth;
      }

      if (stackboxWidth > (windowWidth - minMarginRight)) {
        stackboxWidth = windowWidth - minMarginRight;
      }

      if (stackboxWidth < minWidth) {
        stackboxWidth = minWidth;
      }

      return stackboxWidth;
    },

    autoScroll: function() {

      if (!this.options.autoScroll || this.options.position === 'absolute') {
        return false; // Abort scroll
      }

      var stackboxOffsetTop = this.$stackbox.offset().top,
        wrapperScrollTop = this.$wrapper.scrollTop(),
        windowHeight = $(window).height(),
        windowScrollTop = $(window).scrollTop(),
        stackboxHeight = this.$stackbox.height(),
        padding = 20,
        newScrollTop,
        animOptions = {
          duration: this.options.scrollSpeed,
          easing: this.options.scrollEasing
        },
        firstStackbox = stackboxes[0],
        shouldScrollBody = false,
        i;

      if (firstStackbox && firstStackbox.options.position !== 'absolute') {
        shouldScrollBody = true;
      }

      for (i = 1; i < stackboxes.length; i++) {
        if (stackboxes[i].options.position === 'absolute') {
          shouldScrollBody = false;
        }
      }

      if (shouldScrollBody) {

        if (stackboxOffsetTop < windowScrollTop) { // Top of stackbox is hidden above the window
          $('body,html').animate({
            scrollTop: stackboxOffsetTop - padding
          }, animOptions);

        } else if ((stackboxOffsetTop - windowScrollTop) + stackboxHeight > windowHeight) { // Bottom of stackbox is hidden below the window

          // If the stackbox is taller than the window, scroll to its top (with 20px padding above),
          // otherwise (i.e. the whole stackbox fits inside the window) scroll to its bottom (with 20px padding below).
          if (windowHeight < stackboxHeight) {
            newScrollTop = stackboxOffsetTop - padding;
          } else {
            newScrollTop = stackboxOffsetTop + stackboxHeight - windowHeight + padding;
          }

          $('body,html').animate({
            scrollTop: newScrollTop
          }, animOptions);
        }

      } else {

        if ((stackboxOffsetTop + wrapperScrollTop) < windowScrollTop) { // Top of stackbox is hidden above the window

          this.$wrapper.animate({
            scrollTop: stackboxOffsetTop - padding
          }, animOptions);

        } else if ((stackboxOffsetTop - windowScrollTop) + stackboxHeight > windowHeight) { // Bottom of stackbox is hidden below the window

          // If the stackbox is taller than the window, scroll to its top (with 20px padding above),
          // otherwise (i.e. the whole stackbox fits inside the window) scroll to its bottom (with 20px padding below).

          if (windowHeight < stackboxHeight) {
            newScrollTop = stackboxOffsetTop - windowScrollTop + wrapperScrollTop - padding;
          } else {
            newScrollTop = stackboxOffsetTop - windowScrollTop + wrapperScrollTop + stackboxHeight - windowHeight + padding;
          }

          this.$wrapper.animate({
            scrollTop: newScrollTop
          }, animOptions);
        }
      }
    },

    exitStackbox: function(instant, onClosed) {

      var animDone,
        nextStackbox;

      returnFunction(this.options.beforeClose)(this.$stackbox, this.$offspring, this);
      this.$stackbox.trigger('beforeClose.stackbox', [this.$stackbox, this.$offspring, this]);

      if (this.ajaxRequest) {
        this.ajaxRequest.abort();
      }

      if (stackboxes.length) {
        nextStackbox = stackboxes[stackboxes.length - 2];
        if (nextStackbox) {
          if (nextStackbox.options.closeOnBackdrop === true) {
            nextStackbox.$wrapper.addClass('stackbox-close-on-backdrop');
          } else {
            nextStackbox.$wrapper.removeClass('stackbox-close-on-backdrop');
          }
        }
      }

      if (instant !== true && this.options.animClose) {

        animDone = function animDone() {

          if (this.$offspring) {
            this.$offspring.removeClass('active');
          }

          if ($.isFunction(onClosed)) {
            this.cleanUp();
            onClosed.call(this);
          } else {
            this.cleanUp();
          }
        }.bind(this);

        if (css3animsupported) {
          this.$stackbox.addClass('animated ' + this.options.animClose).off(animationEventNames).on(animationEventNames, animDone);
        } else {
          this.$stackbox.fadeOut(200, function fadeOutDone() {
            animDone();
          });
        }
      } else {

        this.cleanUp();

        if (this.$offspring) {
          this.$offspring.removeClass('active');
        }

        if ($.isFunction(onClosed)) {
          onClosed.call(this);
        }
      }
    },

    cleanUp: function() {

      if (this.$arrow) {
        this.$arrow.remove();
      }

      if (this.$closeButton) {
        this.$closeButton.remove();
      }

      if (this.hadNoScroll === false) {
        $('html').removeClass(this.options.noscrollClass);
      } else {
        $('html').addClass(this.options.noscrollClass);
      }

      window.clearTimeout(this.timeoutID);

      stackboxes.pop();
      stackboxCounter = stackboxes.length;
      domElements.pop();

      returnFunction(this.options.afterClose)(this.$stackbox, this.$offspring, this);
      this.$stackbox.trigger('afterClose.stackbox', [this.$stackbox, this.$offspring, this]);

      if (this.options.returnContent === true && this.returnContent !== undefined) {
        this.$stackbox.children().appendTo(this.returnContent);
      }

      this.$stackbox.remove();

      if (stackboxCounter === 0) {
        this.$wrapperWrapper.remove();
        $('body').css('overflow', 'auto');
      }

      if (this.$wrapper.children().length === 0) {
        this.$wrapper.remove();
        stackboxGroup--;
      }
    },

    toString: function() {
      if (this.created === true) {
        return 'stackbox [#' + this.stackboxIndex + ', g' + this.stackboxGroup + ']';
      } else {
        return 'stackbox [uninitialized]';
      }
    }
  };

  $.fn.stackbox = function(options) {

    var lowercasedOptions = {},
      option;

    if (options === 'close') {
      closeStackboxContainingElement(this);
      return true;
    } else if (options === 'updatePosition') {
      windowResize();
      return true;
    }

    return this.each(function createStackboxObj() {

      for (var i = 0; i < domElements.length; i++) {
        if (this === domElements[i]) {
          console.warn('Stackbox already initialized on element!');
          console.dir(this);
          return false;
        }
      }

      domElements.push(this);

      // Get data-attr, convert to lowercase & remove 'stackbox' prefix
      var dataAttributes = $(this).data(),
        data = {},
        attr,
        propName,
        option,
        optionsKeys;

      for (attr in dataAttributes) {
        if (dataAttributes.hasOwnProperty(attr)) {
          if (attr.indexOf('stackbox') === 0) {
            propName = attr.substr(8);
            propName = propName.charAt(0).toLowerCase() + propName.substr(1);
            if (propName) {
              data[propName] = dataAttributes[attr];
            }
          }
        }
      }

      options = $.extend(data, options);

      optionsKeys = Object.keys(options);

      for (option in optionsKeys) {
        if (optionsKeys.hasOwnProperty(option)) {
          if (!(optionsKeys[option] in $.fn.stackbox.settings)) {
            console.info('Stackbox option "' + optionsKeys[option] + '" is invalid.');
          }
        }
      }

      stackboxes.push(Object.create(stackboxPrototype));
      stackboxCounter = stackboxes.length;
      stackboxes[stackboxCounter - 1].init(options, this);
    });
  };

  $.fn.stackbox.settings = {

    content: false,

    width: 'auto',
    maxWidth: false, // Maximum width when width is in percent.
    minWidth: false, // Minimum width when width is in percent.
    respectBrowserWidth: true,

    scrollSpeed: 600,
    scrollEasing: 'easeOutCirc',

    backdrop: 'auto',
    closeOnBackdrop: true,
    position: 'bottom',
    marginX: 15, // Pixels x-tra away from its relative element. Works more like margin.
    marginY: 5, // Pixels y-tra away from its relative element. Works more like margin.
    nextTo: null, // Place this stackbox next to another element?

    animOpen: 'fadeIn',
    animClose: 'fadeOut',
    mainWrapperClass: 'stackboxes',
    noscrollClass: 'noscroll',
    closeButtonIcon: '&#x2716;',
    spinnerClass: 'loading-spinner',

    autoAdjust: true,
    autoScroll: true, // Scroll to stackbox when opened if outside of (or partically outside of) the window.
    queryParams: null, // Object to send as ajax data.
    requestType: 'GET',
    clone: false,
    returnContent: true, // If true, adds extracted dom content back into the dom tree when closing the stackbox.
    closeButton: true,
    requestFailed: 'Request failed. Please try again.',

    beforeOpen: $.noop,
    afterOpen: $.noop,
    beforeClose: $.noop,
    afterClose: $.noop,
    onError: $.noop
  };

  $(document)
    .on('close.stackbox', closeTopmostStackbox)
    .on('click', '[data-stackbox]', openTrigger);

  $(window)
    .on('resize', windowResize)
    .on('keydown', escapeKeyClick)
    .on('scroll', windowScroll);

  $.extend($.easing, {
    easeOutBack: function(x, t, b, c, d, s) {
      if (s === undefined) {
        s = 1.70158;
      }
      return c * ((t = t / d - 1) * t * ((s + 1) * t + s) + 1) + b;
    },
    easeOutCirc: function(x, t, b, c, d) {
      return c * Math.sqrt(1 - (t = t / d - 1) * t) + b;
    }
  });

  // Check if we have support for CSS3 animations.
  (function() {
    var animationstring = 'animation',
      keyframeprefix = '',
      domPrefixes = 'Webkit Moz O ms Khtml'.split(' '),
      pfx = '';

    if (document.documentElement.style.animationName !== undefined) {
      css3animsupported = true;
    }

    if (css3animsupported === false) {
      for (var i = 0; i < domPrefixes.length; i++) {
        if (document.documentElement.style[domPrefixes[i] + 'AnimationName'] !== undefined) {
          pfx = domPrefixes[i];
          animationstring = pfx + 'Animation';
          keyframeprefix = '-' + pfx.toLowerCase() + '-';
          css3animsupported = true;
          break;
        }
      }
    }
  })();

})(jQuery, window);
