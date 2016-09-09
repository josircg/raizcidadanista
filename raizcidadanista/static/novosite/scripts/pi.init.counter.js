/* Aura version: 1.8.7 */

jQuery(function($){
	"use strict";

	//region piCounter
	if($.fn.piCounter){
		$('.pi-counter').each(function(){
			$(this).one('inview',function(){
				$(this).piCounter();
			});
		});
	}
	//endregion

});