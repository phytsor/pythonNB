@0xb9ee3a18ca954a52;
const qux :UInt32 = 123;


struct Person {
  id @0 :UInt32;
  name @1 :Text;
  attrs @2:List(Attrs);

  struct Attrs{
    name @0:Text;
    number @1:Type;

    enum Type {
      t1 @0;
      t2 @1;
      t3 @2;
    }
  }

  hobby:union {
    h1 @3:Void;
    h2 @4:UInt32;
    h3 @5:Text;
    h4 @9:Text;
  }

  testgroup:group {
    f1 @6:UInt32;
    f2 @7:Text;
    f3 @8:UInt32;
  }

}