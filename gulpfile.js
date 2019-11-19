'use strict';
const path = require('path');
const gulp = require('gulp');
const replace = require('gulp-replace')
const sass = require('gulp-sass');
const sourcemaps = require('gulp-sourcemaps');
const del = require('del');

const PROJECT_DIR = path.resolve(__dirname);
const SASS_FILES = `${PROJECT_DIR}/core/sass/**/*.scss`;
const CSS_DIR = `${PROJECT_DIR}/core/static/styles`;
const CSS_FILES = `${PROJECT_DIR}/core/static/styles/**/*.css`;
const CSS_MAPS = `${PROJECT_DIR}/core/static/styles/**/*.css.map`;

gulp.task('clean', function() {
  return del([CSS_FILES, CSS_MAPS])
});

gulp.task('sass:compile', function () {
  return gulp.src(SASS_FILES)
    .pipe(sourcemaps.init())
    .pipe(sass({
      includePaths: [
        './conf/',
      ],
      outputStyle: 'compressed'
    }).on('error', sass.logError))
    .pipe(sourcemaps.write('./maps'))
    .pipe(gulp.dest(CSS_DIR))
});


gulp.task('sass:fix-static', function () {
  return gulp.src(`${PROJECT_DIR}/core/static/vendor/govuk-frontend-3.2.0.min.css`)
    .pipe(replace('/assets/', '../'))
    .pipe(gulp.dest(CSS_DIR))
});

gulp.task('sass:watch', function () {
  gulp.watch(
    [SASS_FILES],
    gulp.series('sass:compile'),
  );
});

gulp.task('sass', gulp.series('clean', 'sass:compile', 'sass:fix-static'));

gulp.task('default', gulp.series('sass'));
