## CPPCHECK ##
###Bug [#2782](http://trac.cppcheck.net/ticket/2782) ###

#### Bug type :  Non compliance with language specification####

##### Functions involved : ######
 * Token::next in lib/token.h

##### Explanation : #####
in C++, you can define assembly code in your code with #asm {...} #endasm. Cppcheck did not have something to tokenize it, resulting in an import error.
