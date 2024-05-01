import logging

from maya import cmds
import re

from .. import subshotCore
reload(subshotCore)


class MglSubShotSetUI(object):

    def __init__(self, core=None):
        self.core = core
        self.current_win = None
        self.parm_shot = None
        self.parm_subshot = None
        self.scene_path = None
        self.sc_button = None
        self.targeted_subshot = None
        self.shot_code = None
        self.task = None
        self.win_name = "mglSubShotSet"
        self.shot_code, self.task = self.core.check_context()
        self.slave_shots = self.core.get_sub_shots(self.shot_code)
        self.subshot_sets = self.core.get_subshot_sets_with_slave_shots(self.slave_shots, self.shot_code)

    def init_ui(self):
        """
        Set the UI of the current tool.
        """
        btn_width = 110
        btn_height = 30
        # Set window parms and the main layout.
        self.current_win = cmds.window(self.win_name, title=self.win_name, s=False, tlb=True)
        main_layout = cmds.columnLayout(parent=self.current_win, adj=True)
        # Row layout for the shot code content.
        row_shot = cmds.rowLayout(numberOfColumns=2,  h=btn_height, adj=True, cw2=[btn_width, btn_width],
                                       columnAttach=[(1, "both", 5), (2, "both", 5)], parent=main_layout)
        cmds.text("Shot code: ", al="left", font="boldLabelFont", hlc=[1, 0, 0], parent=row_shot)
        self.parm_shot = cmds.textField(text=str(self.shot_code), ed=False, parent=row_shot)
        # Row layout for the targeted subshot content.
        row_subshot = cmds.rowLayout(numberOfColumns=2,  h=btn_height, adj=True, cw2=[btn_width, btn_width],
                                          columnAttach=[(1, "both", 5), (2, "both", 5)], parent=main_layout)
        cmds.text("Subshot targeted: ", al="left", font="boldLabelFont", hlc=[1, 0, 0], parent=row_subshot)
        self.parm_subshot = cmds.optionMenu("targeted_subshot", parent=row_subshot,
                                            ann="Subshot'suffix to target.", cc=self.set_targeted_subshot)
        self.reset_subshot_menu_items()
        # Row layout for the 2 first buttons.
        row_button_a = cmds.rowLayout(numberOfColumns=2, adj=True, parent=main_layout)
        help_set = "Create a pipelined set from the current selection. Replace the existing one if there are."
        cmds.button(label="Set from selection", width=btn_width, height=btn_height, ann=help_set,
                    command=self.set_from_selection, parent=row_button_a)
        help_tip = "Show a popup to give you some tips about this tool."
        cmds.button(label="Quick help", width=btn_width, height=btn_height, bgc=[0.6, 0.7, 0.5], ann=help_tip,
                    c=self.show_help, parent=row_button_a)
        # Row layout for the 2 middle buttons.
        row_button_b = cmds.rowLayout(numberOfColumns=2, adj=True, parent=main_layout)
        help_add = "Add the current selection to the given pipelined set if there is one at least."
        cmds.button(label="Add to set", width=btn_width, height=btn_height, ann=help_add,
                    command=self.add_to_set, parent=row_button_b)
        help_remove = "Remove the current selection to the given pipelined set if there is one at least."
        cmds.button(label="Remove from set", width=btn_width, height=btn_height, ann=help_remove,
                    c=self.remove_to_set, parent=row_button_b)
        # Row layout for the last button.
        row_button_c = cmds.rowLayout(numberOfColumns=2, adj=True, parent=main_layout)
        help_san_check = "Select the components of the targeted sub shot set."
        self.sc_button = cmds.button(label="Select set members", width=btn_width, height=btn_height, ann=help_san_check,
                                     c=self.select_set_members, parent=row_button_c)
        help_san_check = "Launch a sanity check about the content of your subshot sets."
        self.sc_button = cmds.button(label="Sanity Check", width=btn_width, height=btn_height, ann=help_san_check,
                                     c=self.check_and_fix_subshot_sets, parent=row_button_c)

    def callback_check_context(self):
        """
        Compare data scene with the tool's data and refresh the tool's ones if are different.
        """
        # Check the scene context to know if the tool can be used or not.
        self.shot_code, self.task = self.core.check_context()
        # Check if there is slave shots to work with.
        slave_shots = self.core.get_sub_shots(self.shot_code)
        slave_shots.sort()
        if slave_shots == self.slave_shots:
            return
        # If there are slave shots, refresh the UI with them.
        self.refresh_shot()
        self.reset_subshot_menu_items()
        self.subshot_sets = self.core.get_subshot_sets_with_slave_shots(self.slave_shots, self.shot_code)

    def refresh_shot(self):
        """
        Refresh the parm shot of the window with the shot name.
        """
        self.parm_shot = cmds.textField(self.parm_shot, edit=True, text=str(self.shot_code))

    def reset_subshot_menu_items(self):
        """
        Reset menu items and rebuild items inside if there are.
        """
        # Get items from the given option menu parm.
        menuItems = cmds.optionMenu(self.parm_subshot, query=True, itemListLong=True)
        if menuItems:
            # Delete menu items if there are.
            cmds.deleteUI(menuItems, menuItem=True)
        # Build the option menu with new items.
        self.build_subshot_menu_items()
        # Store the first value of the menu.
        menu_value = cmds.optionMenu(self.parm_subshot, query=True, value=True)
        self.set_targeted_subshot(menu_value)

    def build_subshot_menu_items(self):
        """
        Build menu items with subshot names inside if there are.
        """
        if not self.slave_shots:
            return
        # Create menu items.
        self.slave_shots.sort()
        for item in self.slave_shots:
            # Create a menu item from the suffix of each subshot name.
            suffix = re.findall(r"^sq\d{4}_sh\d{4}(\w+$)", item)[0]
            cmds.menuItem(suffix, parent=self.parm_subshot)

    def set_targeted_subshot(self, value):
        """
        Set the targeted subshot value.
        """
        self.targeted_subshot = value

    def set_from_selection(self, *args):
        """
        Create maya set from top nodes of each selected component. Replace the existing one if there is.
        """
        self.callback_check_context()
        new_set = self.core.set_from_selection(self.shot_code, self.targeted_subshot)
        self.subshot_sets[self.targeted_subshot] = new_set

    def show_help(self, *args):
        """
        Create a popup window to give some help to the user.
        """
        message_a = "Why using this tool?\n\nIt allows you to select your components from whatever place you want.\n" \
                    "The set will be built with the top node of each component you have selected and will " \
                    "avoid duplicates between others sub shot sets too."
        message_b = "The tool does not accept: assemblies, sets, non dag objects and children nodes will be replaced."
        message_c = "If you want to manage your sets manually, you have to create a set following this naming " \
                    "convention: <shot name>_<sub shot suffix>, for example 'sq9999_sh1100_B'."
        message_d = "You can access to an quick sanity check directly in the tool. It is the same as the share step one."
        message_e = "WARNING:\n'Duplicated/Missing' parts cannot be auto fixed.\nShare before building the sub shots."
        final_message = "{}\n{}\n\n{} {}\n\n{}".format(message_a, message_b, message_c, message_d, message_e)
        default = "Close"
        cmds.confirmDialog(title="Quick help !", message=final_message, button=[default], defaultButton=default,
                           cancelButton=default, icon="information")

    def add_to_set(self, *args):
        """
        Add the top node of each selected component on the given maya set.
        """
        # Check the scene context to know if the tool can be used or not.
        self.callback_check_context()
        # Add the current selection to the given subshot set.
        updated_set = self.core.add_to_set(self.targeted_subshot, self.shot_code)
        self.subshot_sets[self.targeted_subshot] = updated_set

    def remove_to_set(self, *args):
        """
        Remove selected components from the given maya set.
        """
        # Check the scene context to know if the tool can be used or not.
        self.callback_check_context()
        # Remove the current selection from the given subshot set.
        updated_set = self.core.remove_to_set(self.targeted_subshot, self.shot_code)
        self.subshot_sets[self.targeted_subshot] = updated_set

    def select_set_members(self, *args):
        """
        Select the components of the targeted sub shot set.
        """
        targeted_set = self.subshot_sets.get(self.targeted_subshot)
        self.core.select_set_members(targeted_set)

    def check_and_fix_subshot_sets(self, *args):
        """
        Check the content of the subshot set and fix it if asked.
        """
        default = "Close"
        fix = "Fix"
        title = "Sanity Check Report"
        # Check the content of each sub shot sets.
        check_report = self.core.check_subshot_content(self.subshot_sets)
        message = check_report.get("message")
        print("\nSANITY CHECK REPORT {}\n{}{}".format("-"*80, message, "-"*100))
        # Show a popup to summarize to report of the check.
        if check_report["state"]:
            self.sc_button = cmds.button(self.sc_button, edit=True, bgc=[0.6, 0.7, 0.5])
            self.core.show_popup_dialog(message, title, icon="information")
            return
        self.sc_button = cmds.button(self.sc_button, edit=True, bgc=[0.6, 0.1, 0.1])
        user_input = cmds.confirmDialog(title=title, message=message, button=[fix, default],
                                        defaultButton=fix, cancelButton=default, icon="error")
        # If we have a check report, the popup show a new fix function.
        if user_input == fix:
            fix_report = self.core.fix_subshot_content(check_report)
            if fix_report["state"]:
                self.sc_button = cmds.button(self.sc_button, edit=True, bgc=[0.6, 0.7, 0.5])
                self.core.show_popup_dialog("Congrats.\n\nEverything is okay.\nReady to build the sub shots.")
            else:
                self.core.show_popup_dialog("Everything has been corrected on your sub shot sets.\n"
                                            "Do not forget to manage your duplicated/missing elements on your sets.")

    def show(self):
        """
        Show the window, and delete the existing one before if there is.
        """
        # Check if the window is unique.
        if cmds.window(self.win_name, query=True, exists=True):
            # Delete UI and its preferences if it exists.
            cmds.deleteUI(self.win_name, wnd=True)
            cmds.windowPref(self.win_name, removeAll=True)
        # Set the UI and show it.
        self.init_ui()
        cmds.showWindow(self.current_win)


def launcher():
    """
    Launch the UI and its functions.
    """
    global MGL_SUBSHOT_SET
    core = subshotCore.MglSubShotSet()
    MGL_SUBSHOT_SET = MglSubShotSetUI(core)
    MGL_SUBSHOT_SET.show()
