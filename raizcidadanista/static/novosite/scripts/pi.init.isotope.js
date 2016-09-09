/* Aura version: 1.8.7 */

jQuery(function($){
	"use strict";

	//region Isotope
	if($.fn.isotope) {

		var $w = $(window);

		$w.load(function () {
			var $isotops = $('.isotope');

			$isotops.each(function () {
				var $el = $(this),
					defaultFilter = $el.data('isotopeDefaultFilter') || 0,
					id = $el.attr('id'),
					mode = $el.data('isotopeMode') || 'fitRows',
					tmt;


				$el.isotope({
					filter: defaultFilter,
					itemSelector: '.isotope-item',
					layoutMode: mode,
					getSortData: {
						name: '.name',
						category: '[data-category]'
					},
					animationOptions: {
						duration: 400,
						queue: false
					}
				});

				$el.get(0).piIsotopeFilters = [];


				$w.resize(function(){
					clearTimeout(tmt);
					tmt = setTimeout(function(){
						$el.isotope('layout');
					}, 1000);
				});

				$('[data-isotope-nav="' + id + '"]').on('click', 'a', function (e) {

					var $link = $(this);
					if(!$link.hasClass('pi-active')){
						var filter = $link.attr('data-filter'),
							sorter = $link.attr('data-sort-value');

						$link.parents('ul').eq(0).find('.pi-active').removeClass('pi-active');
						$link.addClass('pi-active');

						if(filter){

							var filterGroup = $link.parents('[data-filter-group]'),
								filtersList = $el.get(0).piIsotopeFilters,
								activeFilters = '';

							if(filterGroup.length){
								filterGroup = filterGroup.attr('data-filter-group');
							} else {
								filterGroup = 'piIsotopeMainFilterGroup';
							}

							filtersList[filterGroup] = filter;

							for ( var i in filtersList ) {
								if(filtersList.hasOwnProperty(i)){
									activeFilters += filtersList[i];
								}
							}

							$el.isotope({ filter: activeFilters });
						} else if(sorter) {
							$el.isotope({ sortBy: sorter });
						}
					}
					e.preventDefault();
				});

				$w.resize();

			});

		});

	}
	//endregion

});