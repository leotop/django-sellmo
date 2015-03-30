(($, window) ->

  class CopyAddress

    defaults: {
      fromSelector: '#shipping-address',
      toSelector: '#billing-address',
    }

    constructor: (el, options) ->
      @options = $.extend({}, @defaults, options)
      @$el = $(el)
      @$from = $(@options.fromSelector)
      @$to = $(@options.toSelector)
      
      @$from.on 'change', =>
        @update()
      
      @$el.on 'change', =>
        @update()
      @update()
    
    update: () ->
      if @$el.is(':checked')
        @$to.hide()
        $('input', @$from).each (i, el) ->
          # field must be the first css class defined
          selector = 'input.' + $(el).attr('class').split(' ')[0]
          $(selector, @$to).val($(selector, @$from).val())
      else
        @$to.show()


  $.fn.extend copyAddress: (option, args...) ->
    @each ->
      $this = $(this)
      data = $this.data('copyAddress')
      if !data
        $this.data 'copyAddress', (data = new CopyAddress(this, option))
      if typeof option == 'string'
        data[option].apply(data, args)


) window.jQuery, window