# scanClazz

<font color=darkgreen>
NOTE:     
    If local graphviz has installed, and script is launched with python3;     
    Then graph png will be generated automatically with local installed graphviz dot/fdp engine.

    The generated png will be under `~/Downloads/`, named as `graph-dot.png` and `graph-fdp.png`.
</font>

## generate class relationship for graphviz

```
Usage: python scan_clazz.py -p dir_to_scan [options]

    Options:
    -m mode
            mode can be 'c' 'i' 'r', or combine
            'c' - parsing class and inherit
            'i' - parsing interface and implement (NOT supported)
            'r' - parsing relationship between classes (used by)
    -e class[,class2,class3,...,classn]
            exclude classes in parsing result
    -k class
            assign the key class which will be emphasized in output
    -d depth
            take effect only if key class is assigned
            valid depth must be a integer between [3-9], include 3 and 9
            otherwise depth will be discarded
            depth is calculated from key class, a class direct rely on / relied by key class has depth 1 
```

### sample

```
python scan_clazz.py -p /Users/lego/aosp/packages/apps/Calendar/ -e Button,View,Activity,Utils,Drawable,TestCase,Fragment,FrameLayout,ListFragment,ListView,ListActivity -m icr -k MonthByWeekFragment
```

### output

file `output` will be generated under `dir_to_scan`

## draw relationship with graphviz

copy the output from last step, and draw with graphviz, you can use [Graphviz Online Editor](https://edotor.net)

### drawed sample - aosp calendar with unlimited depth

scan cmd

```
python scan_clazz.py -p /Users/lego/aosp/packages/apps/Calendar/ -e Button,View,Activity,Utils,Drawable,TestCase,Fragment,FrameLayout,ListFragment,ListView,ListActivity -m icr -k MonthByWeekFragment
```

**dot**

![](http://ww2.sinaimg.cn/large/006tNc79ly1g3kyi2unonj32770u0h96.jpg)

**fdp**

![](http://ww4.sinaimg.cn/large/006tNc79ly1g3kyig69cjj30u00yk7wh.jpg)

### drawed sample - aosp calendar with depth up to 3

scan cmd

```
python scan_clazz.py -p /Users/lego/aosp/packages/apps/Calendar/ -e Button,View,Activity,Utils,Drawable,TestCase,Fragment,FrameLayout,ListFragment,ListView,ListActivity -m icr -k MonthByWeekFragment -d 3
```

**dot**

![](http://ww1.sinaimg.cn/large/006tNc79ly1g3ly7525nyj311z0u0476.jpg)

**fdp**

![](http://ww1.sinaimg.cn/large/006tNc79ly1g3ly7iaikkj31cz0u0qbv.jpg)
