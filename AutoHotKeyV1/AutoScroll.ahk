; AutoHotkey v2 script for toggling auto-scrolling with Ctrl+Down and Ctrl+Up

; Set scrolling speeds (in milliseconds)
global ScrollSpeedDown := 110  ; Scrolling down speed (smaller value = faster)
global ScrollSpeedUp := 110    ; Scrolling up speed (smaller value = faster)

; Global variables to track the scrolling state
global ScrollDownThread := False  ; Initialize ScrollDownThread as global and set it to False
global ScrollUpThread := False    ; Initialize ScrollUpThread as global and set it to False
global TooltipDuration := 1000    ; Duration for ToolTip display (in milliseconds)

; Toggle auto-scrolling down with Ctrl+Down
^Down::
{
    global ScrollDownThread, ScrollUpThread, ScrollSpeedDown, TooltipDuration  ; Ensure global variables are recognized
    ScrollDownThread := !ScrollDownThread  ; Toggle the ScrollDownThread variable

    if ScrollDownThread
    {
        ToolTip("Auto-scrolling down started")
        SetTimer(ClearToolTip, TooltipDuration)  ; Set a timer to clear the tooltip
        ScrollUpThread := False  ; Ensure upward scrolling is stopped
        SetTimer(ScrollPageDown, ScrollSpeedDown)  ; Start the timer to scroll down using the set speed
        SetTimer(ScrollPageUp, 0)  ; Turn off upward scrolling
    }
    else
    {
        ToolTip("Auto-scrolling down paused")
        SetTimer(ClearToolTip, TooltipDuration)  ; Set a timer to clear the tooltip
        SetTimer(ScrollPageDown, 0)  ; Turn off the timer
    }
}

; Toggle auto-scrolling up with Ctrl+Up
^Up::
{
    global ScrollUpThread, ScrollDownThread, ScrollSpeedUp, TooltipDuration  ; Ensure global variables are recognized
    ScrollUpThread := !ScrollUpThread  ; Toggle the ScrollUpThread variable

    if ScrollUpThread
    {
        ToolTip("Auto-scrolling up started")
        SetTimer(ClearToolTip, TooltipDuration)  ; Set a timer to clear the tooltip
        ScrollDownThread := False  ; Ensure downward scrolling is stopped
        SetTimer(ScrollPageUp, ScrollSpeedUp)  ; Start the timer to scroll up using the set speed
        SetTimer(ScrollPageDown, 0)  ; Turn off downward scrolling
    }
    else
    {
        ToolTip("Auto-scrolling up paused")
        SetTimer(ClearToolTip, TooltipDuration)  ; Set a timer to clear the tooltip
        SetTimer(ScrollPageUp, 0)  ; Turn off the timer
    }
}

; Function to handle scrolling down
ScrollPageDown()
{
    global ScrollDownThread  ; Ensure ScrollDownThread is recognized as global
    if ScrollDownThread
    {
        Send("{WheelDown}")  ; Send the WheelDown event to scroll down
    }
}

; Function to handle scrolling up
ScrollPageUp()
{
    global ScrollUpThread  ; Ensure ScrollUpThread is recognized as global
    if ScrollUpThread
    {
        Send("{WheelUp}")  ; Send the WheelUp event to scroll up
    }
}

; Function to clear the ToolTip after the specified duration
ClearToolTip()
{
    ToolTip("")  ; Clear the tooltip
}
