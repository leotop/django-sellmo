(($, window) ->

  class ProductAvailability

    defaults: {
      availabilitySelector: '.product-availability',
      templateSelector: '#product-availability-template',
      template: null,
      stocks: null,
      delays: null,
      stock: null,
      delay: null,
    }

    constructor: (el, options) ->
      @options = $.extend({}, @defaults, options)
      @$el = $(el)
      
      if not @options.template
        template = $(@options.templateSelector).html()
      else
        template = $(@options.template)
      
      # Compile template and keep ref
      @template = Handlebars.compile(template);
      
      # Initialize state
      @updateAvailability()
    
      # Find variation select
      @$variation = $('select.variation', @el)
      
      # Try to find first option to be in stock
      $('option', @$variation).each (i, option) =>
          $option = $(option)
          key = $option.val()
          stock = @options.stocks[key]
          if stock > 0
              @$variation.val(key)
              @updateAvailability()
              return false
      
      # Handle user input
      @$variation.on 'change', (evt) =>
          @updateAvailability()
      
    updateAvailability: () ->
      
      if @options.stocks != null
          select = $('select.variation', @$el)
          key = select.val()
          stock = @options.stocks[key]
          delay = @options.delays[key]
      else
          stock = @options.stock
          delay = @options.delay
    
      if stock > 0
          # Enable add to cart button
          $('input[type=submit]', @$el).removeAttr('disabled', 'disabled')
      else
          # Disable
          $('input[type=submit]', @$el).attr('disabled', 'disabled')
    
      context = {stock: stock, delay: delay}
      $(@options.availabilitySelector, @$el).html(@template(context))
       

  $.fn.extend productAvailability: (option, args...) ->
    @each ->
      $this = $(this)
      data = $this.data('productAvailability')

      if !data
        $this.data 'productAvailability', (data = new ProductAvailability(this, option))
      if typeof option == 'string'
        data[option].apply(data, args)
        

) window.jQuery, window