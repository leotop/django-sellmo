var gulp = require('gulp');
var less = require('gulp-less');
var util = require('gulp-util');


var paths = {
  less: {
    entries:  ['./src/less/screen.less', './src/less/print.less'],
    watch: ['./src/less/**/*.less']
  }
}

var onError = function(err) {
  util.log(util.colors.red(err));
  util.beep();
  this.emit('end');
}

gulp.task('less', function() {
  var src = gulp.src(paths.less.entries)
    .pipe(less())
    .on('error', onError)
    .pipe(gulp.dest('./build/css'))
});


gulp.task('watch', function() {
  gulp.watch(paths.less.watch, ['less']);
});
