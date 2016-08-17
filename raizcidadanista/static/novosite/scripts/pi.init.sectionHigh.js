/* Aura version: 1.8.7 */

jQuery(function($){
	"use strict";

	//region Section Full Height
	var $w = $(window),
		$sections = $('.pi-section-high, .pi-block-high'),
		resizeTMT;

	$w.resize(function(){
		clearTimeout(resizeTMT);
		resizeTMT = setTimeout(function(){
			setSectionHeight();
		}, 100);
	});

	function setSectionHeight(){
		$sections.each(function(){
			var $el = $(this);
			$el.height(window.piViewportHeight);
		});
	}

	setSectionHeight();

	//endregion

});