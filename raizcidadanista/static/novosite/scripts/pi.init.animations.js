/* Aura version: 1.8.7 */

jQuery(function ($) {
	"use strict";

	//region init animations
	$('[data-animation]').each(function () {

		var $el = $(this),
			animationType = $el.data('animation'),
			animationDelay = $el.data('animationDelay') || 1,
			animationDirection = animationType.indexOf('Out') >=0 ? 'back' : 'forward';
		
		if(animationDirection === 'forward'){
			$el.one('inview', function () {
				setTimeout(function () {
					$el.addClass(animationType + ' visible');
				}, animationDelay);
			});
		} else {
			$el.addClass('visible');
			$el.one('click', function () {
				setTimeout(function () {
					$el.addClass(animationType);
				}, 0);
			});
		}

	});
	//endregion


});