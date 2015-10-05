## Cppcheck ##
###Bug [#3238](http://sourceforge.net/apps/trac/cppcheck/ticket/3238) ###

#### Bug type : segmentation fault (null pointer access) ####

##### Functions involved : ######
 * CheckObsoleteFunctions::obsoleteFunctions() in lib/checkobsoletefunctions.cpp


##### Explanation : #####
The bug occurs in `if ((tok->next()->link()->next() && tok->next()->link()->next()->str() == ";") && (tok->previous()->str() == "*" || tok->previous()->isName()))`
where tok->previous() is not checked not to be `Null` before being accessed. If this is the case, the program will therefore segfault.