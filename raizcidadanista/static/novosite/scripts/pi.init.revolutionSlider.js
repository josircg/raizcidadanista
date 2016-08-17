/* Aura version: 1.8.7 */

jQuery(function($){
	"use strict";

	//region Revolution Slider
	if($.fn.revolution){
		$('.pi-revolution-slider').revolution({
			delay:9000,
			startwidth:1130,
			startheight:500,
			hideThumbs:10,
			fullWidth:"on",
			forceFullWidth:"off",
			hideTimerBar:"on"
		});

		$('.pi-revolution-slider-fullscreen').revolution({
			delay:9000,
			startwidth:1130,
			startheight:500,
			hideThumbs:10,
			fullScreen:"on",
			hideTimerBar:"on"
		});

		$('.pi-revolution-slider-fullscreen-offset-header').revolution({
			delay:9000,
			startwidth:1130,
			startheight:500,
			hideThumbs:10,
			fullScreen:"on",
			hideTimerBar:"on",
			fullScreenOffsetContainer:".pi-header"
		});
	}
	//endregion

});

