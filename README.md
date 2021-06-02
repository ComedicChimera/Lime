# lime

**Lime** is an esoteric programming language based on lambda calculus. 

If you prefer to learn by example, try checking out the `examples` folder after
doing some cursory reading of the first two parts of this file.

## Table of Contents

- [Running Lime](#run)
- [Language Basics](#basics)
- [Builtin Functions](#builtins)
- [Laziness](#laziness)
- [Recursion](#recursion)

## <a name="run"> Running Lime

The Lime interpreter is written in Python and can be run from the file
`lime.py`.  It accepts a single command line argument which is the filename to
run.

    python lime.py [filename]

All Lime files conventionally end with the extension `.lime` (although they do
not technically have to).

## <a name="basics"> Language Basics

Lime is dynamically but strongly typed and supports 5 fundamental data types:

| Type | Description | Examples |
| ---- | ----------- | -------- |
| number | A floating point number | `4`, `5.6` |
| string | A unicode string | `"abc"`, `"hello there!\n"` |
| list | A list of values | `[5, 6, 7]`, `["hello", 5]` |
| function | A first-class function (curried) | *see below for examples* |
| none | A value representing nothing | `()` |

Line comments can be written starting with `;`

    ; comment

The core building blocks of Lime programs are functions.  Functions are
first-class types in Lime and are *curried* by default.  To create a function,
you use the `\` (lambda) followed by the name of an argument, a `.`, and an
expression.

    \a.a ; identity function

If a function takes multiple arguments, you can simply include multiple argument
definitions one after the other.

    \a.\b.expr

You can call a function by simply placing an argument next to a function.

    (\a.a) 5 ; => 5

Notice that function calls in Lime are left associative.  This means that the
language will always prioritize building the leftmost call.  For example,

    f g h

Calls `f` on `g` and then on `h` (ie. `(f g) h`).  So, if you have expressions
are arguments within a function call, make sure to wrap them in parentheses.

    f (g h)

Lime functions are also curried which means that a function when called without
all of its arguments simply yields an inner, "partial" function.

    (\a.\b.a b) f ; => \b.f b

In fact, any function call with multiple arguments is actually interpreted as a
series of partial function calls -- the last call to a curried function
evaluates it.

    f g h ; => (f g) h
    (\a.\b.a b) f g ; => ((\a.\b.a b) f) g => (\b.f b) g => f g

You can *bind* variables in Lime using the `:=` syntax.

    call := \a.\b.a b
    x := 4 ; anything can be a variable

`call` and `x` can then be referenced anywhere in your program.  Note that a
variable cannot be referenced until it is bound including within its own
binding.  So the following is invalid:

    call := \x.call x ; `call` is undefined

Variables can be rebound after they have been created.

    x := 56
    ; -- snip --
    x := 22

Note that any series of non-reserved symbols that doesn't start with a digit can
be an identifier.  So we can create bindings to operators like so:

    $ := \a.\b. a b
    a+b := 6 ; `a+b` is a distinct identifier
    my_var := "test"
    HELLO! := "hello"
    v12 := 12

An identifier ends whenever it encounters whitespace or some reserved character.

Finally, the execution of Lime programs proceeds line by line with each
expression being evaluated and printed and each binding being evaluated but not
printed in any way.  Lime expressions can not be split across multiple lines.

    pick_first := \a.\b.a ; nothing is printed

    pick_first 5 4 ; prints `5`

Because of this, writing a hello world program is trivial in Lime.

    "Hello, world!"

## <a name="builtins"> Builtin Functions

Lime provides several builtin functions for doing common operations on its
builtin data types.

For numbers, it provides all 5 standard arithmetic operators: `+`, `-`, `*`,
`/`, and `%`.  Note that these operators are functions and so must be used
in reverse polish notation.

    + 5 4 ; => 9
    * 12.3 6.5 ; => 79.95
    % 6.5 1 ; => 0.5

Note that with these operators in particular spacing is important because of the
aforementioned identifier rules: `+ab` is an identifier not an expression.

For strings, it provides the `cat` (for string concatenation) and the `at` (for
string indexing) functions.

    cat "hello " "there" ; "hello there"
    at "hello" 0 ; "h"

For lists, a similar set of functions exists: `join` (for list concatenation)
and `at` (for list indexing; same function works for both strings and lists).

    join [5, 4] ["test", 1] ; [5, 4, 1, "test"]
    at [6, 7] 1 ; 1

Lime also provides three comparison operators: `=` (equality), `<` (less than),
and `>`.  In the absence of a boolean type, these functions take 4 arguments:
the two values to compare, a value to return if the comparison succeeds, and a
value to return if it doesn't.

    = 5 5 "equal" "not equal" ; "equal"
    < 78 2 "true" "false" ; "false"

There are two notable casting functions: `num` and `str` -- these will convert a
string to a number and a number to a string respectively.  

    num "56" ; => 56
    str 3.4 ; => "3.4"

Finally, to perform standard IO, Lime provides two functions and secondary
helper function to manage side-effects.  In conventional lambda calculus,
operations such as getting input are effectively impossible; however, Lime
chooses to allow side-effects in this special case so we can build slightly more
useful programs.

The first function is `get` which gets a value from the console.  This function
takes no arguments (which is technically not possible within Lime) so to call it
we pass in `()` (nothing) as a work around.

    get() ; prompts user for input.

The next two functions tend to work together.  The first of these two functions
is `print` which may seem somewhat redundant given that Lime will automatically
print each expression when it is evaluated.  However, it is occasionally useful
to print during the evaluation of a complex expression and so this function
allows you to do that.

    print "Hello, world!" ; prints "Hello, world!" and returns `()`

The final builtin function is the function `do` which evaluates both its
arguments and returns the result of the final argument.  This function is useful
when you want to do something (eg. `print`) and then evaluate something else. 

Using these three functions, we can be build a simple `prompt` function (like
Python's `input`).

    prompt := \msg. do (print msg) (get())

    ; prints "Enter your name:" and returns the user's input
    prompt "Enter your name:"

## Laziness

Laziness is the principle that states that Lime will not evaluate an expression
until it needs to be evaluated (if at all).

This principle of laziness is most visible in functions like `=` where the only
expression that will ever actually be evaluated is the expression returned.

    = 0 2 (print "true") (print "false") ; only "false" is printed

Note that laziness will not effect how expressions are evaluated once Lime
decides to evaluate them -- ie. the expression will always be evaluated in the
correct context.

    g := \n.(* n 4)
    f := \n.= n 2 (- n 2) (g (+ n 2))

    f 3 ; => = 3 2 (- 3 2) (g (+ 3 2)) => (g (+ 3 2)) => (* (+ 3 2) 4) => 20

If the above statement seems logical to you (or you don't understand when that
wouldn't be true), great -- that is the idea; laziness in Lime is supposed to be
logical.

Laziness might seem like a strange quirk of the language, but it is absolutely
essential to facilitating effective recursion -- the last topic in our tour of
Lime.

## Recursion

The final topic in Lime is recursion which isn't so much a feature as it is
technique.  You may have noticed at this point that Lime has no builtin way to
loop.  That is because in Lime, we don't use loops: we use recursion.

However, if you are familiar with how other languages approach recursion, it is
most common to recur via calling a function by its name within its body.  As we
have seen earlier, that is not possible in Lime since values are bound after
they are used.

    rec := \x.rec x ; error: `rec` is not defined

Therefore, we must find another approach to recursion -- specifically, we need
to find a way to recur without referencing the function name in our recursion.
You might not think that is possible, but in fact, it is.

In order to do recursion in Lime, you need to something called the
*Y-combinator*.  For our purposes, the Y-combinator is pattern that can be used
to generate recursive functions. 

The premise of the Y-combinator is that we essentially pass a function itself as
an argument and then have it call itself within itself via that argument.

Let's examine what this looks like using an example: the factorial function. For
those unfamiliar factorial of an integer is defined as the product of the all
the numbers greater than zero up untit and including that integer.  So, the
factorial of `5` is `5 * 4 * 3 * 2 * 1` or, more relevant to our purposes, `5 *
4!` where `!` denotes "the factorial of" the preceding integer.  Notice that
this process is inherently recursive: we call factorial with again with `n-1`
inside its body.  We could define factorial in psuedocode as looking like:

```python
def factorial(n):
    if n == 1:
        return n
    
    return n * factorial(n-1)
```

Notice that we have two cases: a base case and a recursive case.  The trick is
simply the recursive case.

As mentioned before, to accomplish recursion in Lime, we are going to pass a
function to itself as an argument and then call that argument within the
function.  For sake of convenience, we are going to split the factorial function
into its two parts: the recursive core and the full definition.  

Starting with the core of the function:

    fact_rec := \f.\n.= n 1 n (f f (- n 1))

It is best to break this definition down into pieces to understand it.  First,
the signature of the function is `\f.\n.`.  The first argument is the going to
be our "self-reference" and the second is the value we are computing the
factorial of.  We know that when we build our final factorial function, the
self-reference is going to `fact_rec`.  

Next, we have our equality operator which compares `n` to `1`.  Notice how
important laziness is to this definition: our recursive case (when `n` is not
`1`) is only evaluated if the equality operator determines that the function
should recur -- otherwise, we would end up caught in an infinite loop of
evaluation.

The base case is simply just `n` which matches up with our psuedocode above.

Finally, we examine the recursive case.  This case calls `f` which we know will
be `fact_rec` with `f` (calling `fact_rec` with itself) and then passes in `n - 1` 
as to that recursive call -- decrementing `n` on each iteration.

Now, we can conclude by building the final definition of `fact` which is simply
going to be:

    fact := fact_rec fact_rec

Because functions curry automatically in Lime, `fact` is now a single argument
function that takes an `n` and returns its factorial.  Notice that our
expression for `fact` matches our recursive call in our definition of
`fact_rec`.  If we perform a little argument substitution, we can see that
recursion emerges.

    fact = fact_rec fact_rec 
         = (\f.\n.= n 1 n (f f (- n 1))) fact_rec
         = \n.= n 1 n (fact_rec fact_rec (- n 1))
         = \n.= n 1 n (fact (- n 1)) ; boom -- recursion!

Now, you should be able to see how we are able to obtain recursion using
laziness and a special pattern.  If you run `fact 5`, you should get `120` back
which is the correct factorial.

Recursion in Lime (and lambda calculus in general) can be difficult, but
hopefully this gives you a good starting point for understanding recursion.  You
can practice by trying to implement other recursive functions (or other kinds of
loops).



    



