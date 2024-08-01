;
SetTimer(MoveMouse, 300000) ;

MoveMouse() {
    static toggle := true
    if toggle {
        MouseMove(1, 0) ;
    } else {
        MouseMove(-1, 0) ;
    }
    toggle := !toggle
}

OnExit(ObjBindMethod(ExitFunc, "Call"))

ExitFunc() {
    ExitApp()
}
