/* Aura version: 1.8.7 */

jQuery(function($){
	"use strict";

	var activeLink = window.location.href.match(/\/([^\/]*)$/);

	if(activeLink){

		$('.pi-header-sticky .pi-simple-menu a').each(function(){
			var $el = $(this);
			if($el.parent().hasClass('active')) {
				$el.parent().removeClass();
			}
			if($el.attr('href').indexOf(activeLink[1]) >= 0) {
				$el.parent().addClass('active');
			}
		});

	}

});