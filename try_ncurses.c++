#include <curses.h>
#include <locale.h>
#include <strings.h>
#include <string>

int main(int argc, char const *argv[]) {
    setlocale(LC_ALL, "");
    initscr(); cbreak(); noecho(); nonl(); // init stuff for curses
    keypad(stdscr, TRUE); // set stdscr to listen to the keyboard.
    std::string output = "Hello World!";
    int move_success = wmove(
      stdscr,
      (int)(COLS-strlen(output.c_str()))/2,
      LINES/2            // <-^^ center the cursor before
    );
    std::string finout;
    if (move_success == ERR){
      finout = "Error moving cursor";
    } else {
      wprintw(stdscr, output.c_str());
      refresh();   // which isn't applied until refresh is called.
      int recvd = getch();
      finout = std::to_string(recvd);
    }
    nocbreak(); echo(); // teardown stuff for curses
    endwin();
    printf(
      "%s\nAttempted position: %d by %d\n",
      finout.c_str(),
      (int)(COLS-strlen(output.c_str()))/2,
      LINES/2
    );
    return 0;
}
