-> top_knot

CONST COFFEE_BRAND = "Roastini"

=== top_knot ===
Hello World # Good moring
How are you?
* Fine[, I guess].
  That's good. -> coffee_time
  -> END
* Meh.
  Hmm that's too bad. -> coffee_time
  
 === coffee_time ===
 VAR takes_cream = false
 VAR takes_sugar = false
 Would you like a cup of coffee? We serve {COFFEE_BRAND}.
 * Sure.
    - - (cream)
    Cream and sugar?
    * * Just cream.
    ~ takes_cream = true
    * * A little sugar.
    ~ takes_sugar = true
    * * Both.
    ~ takes_cream = true
    ~ takes_sugar = true
    - - Ok
 * Decaf for me.
    If you insist. <> -> cream
 * Double espresso?
 
- Here you go. 
Your coffee arrives. 
{ takes_cream:
    <> It is smooth and milky.
}
{ takes_sugar: 
    <> It tastes a bit like candy.
}
  
  -> END