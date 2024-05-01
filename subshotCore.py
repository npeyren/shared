import logging

import maya.cmds as cmds
import re
import sgtk

import mglImport
import mglPymel as pymel
from pipeline.mglMayaScene.tdTools.general import assembly_tools


class MglSubShotSet(object):
    """
    Callback class for the mglSubShotSet tool.
    """

    def __init__(self):
        self.engine = sgtk.platform.current_engine()
        self.tasks = ("lay", "ani")

    def is_subshot(self, shot_code=None):
        """
        Detect if you are in sub shot context.
        :param shot_code: name of the shot
        :type shot_code: str
        :returns: True if you are in sub shot context
        :rtype: bool
        """
        if not shot_code:
            try:
                engine = self.engine
                shot_code = engine.context.entity["name"]
            except Exception:
                message = "Non pipelined scene. Please save this scene or open a pipelined one. Continue the process."
                logging.error(message)
                return
        # Check the shot name to know if we are in a sub shot. A sub shot has to contain a letter as suffix.
        is_subshot = re.match(r"^sq\d{4}_sh\d{4}\w$", str(shot_code))
        if is_subshot:
            return True
        return False

    def is_parent_shot(self, shot_code=None):
        """
        Detect if you are in parent shot context.
        :param shot_code: name of the shot
        :type shot_code: str
        :returns: True if you are in sub shot context
        :rtype: bool
        """
        if not shot_code:
            try:
                engine = self.engine
                shot_code = engine.context.entity["name"]
            except Exception:
                message = "Non pipelined scene. Please save this scene or open a pipelined one. Continue the process."
                logging.error(message)
                return
        has_subshot = self.get_sub_shots(shot_code)
        if has_subshot:
            return True
        return False

    def check_context(self, on_subshot=False, custom_raise=True, return_values=False):
        """
        Check and set the scene context to know if the tool can be used or not.
        :param on_subshot: Consider that we are on sub shot context or not
        :type on_subshot: bool
        :param custom_raise: allow a raise and a window with the same message
        :type custom_raise: bool
        :param return_values: allow to return values instead of raising
        :type return_values: bool
        :returns: shot name and task
        :rtype: tuple(str)
        """
        # Get the shot name and task from the current engine.
        shot_code, task = self.get_shot_code_and_task_from_engine()
        if not shot_code:
            message = "Pipeline Sub shot: Has to be used in pipelined scenes only, not untitled."
            if return_values:
                logging.error(message)
                return None, None
            elif custom_raise:
                self.custom_raise(message)
            raise RuntimeError(message)
        # Check the scene context to know if the tool can be used or not.
        is_subshot = bool(re.match(r"^sq\d{4}_sh\d{4}\w$", str(shot_code)))
        has_sub_shots = self.get_sub_shots(shot_code)
        if not on_subshot:
            if task not in self.tasks or is_subshot or not has_sub_shots:
                message = "Pipeline Sub shot: This part has to be used in layout/animation tasks and on parent shots only."
                if return_values:
                    logging.error(message)
                    return None, None
                elif custom_raise:
                    self.custom_raise(message)
                raise RuntimeError(message)
        elif task not in self.tasks or not is_subshot:
            message = "Pipeline Sub shot: This part has to be used in layout/animation tasks and on sub shots only."
            if return_values:
                logging.error(message)
                return None, None
            elif custom_raise:
                self.custom_raise(message)
            raise RuntimeError(message)
        return shot_code, task

    def get_shot_code_and_task_from_engine(self, engine=None):
        """
        Get the template and its fields from a given path.
        :param engine: current engine
        :type engine: Sgtk engine
        :returns: shot name and task
        :rtype: tuple(str)
        """
        if not engine:
            engine = self.engine
        # Get the shot name and task from the current engine.
        shot_code = engine.context.entity["name"]
        task = engine.context.task["name"]
        if not shot_code or not task:
            cmds.error("Non pipelined scene.\nPlease save this scene or open a pipelined one.")
        return shot_code, task

    def get_sub_shots(self, shot_code=None):
        """
        Get the sub shot info depending on the shot.
        :param shot_code: name of the shot
        :type shot_code: str
        :returns: slave shot names
        :rtype: list[str]
        """
        # Query the shot info from the shot name and the current task.
        context = self.engine.context
        if not shot_code:
            shot_code = context.entity["name"]
        sub_shot_field = "shots"
        sg_filters = [
            ["project", "is", context.project],
            ["code", "is", shot_code],
            ["sg_status_list", "is_not", "omit"]]
        data_shot = self.engine.shotgun.find("Shot", filters=sg_filters, fields=[sub_shot_field])
        if not data_shot:
            logging.info("No sub shots found. Please verify the shot info on Shotgrid.")
            return
        # Get the name of the slave shots.
        slave_shots = [slave.get("name") for slave in data_shot[0][sub_shot_field]]
        return slave_shots

    def get_subshot_sets_with_slave_shots(self, slave_shots, shot_code):
        """
        Get sub shot set created in the scene and store them in a dict.
        :param slave_shots: slave shot names
        :type slave_shots: list[str]
        :param shot_code: name of the shot
        :type shot_code: str
        :returns: store set name by slave shot found. (ie: {'B': None, 'C': 'sq9999_sh1100_C_ani'})
        :rtype: dict
        """
        # Create a dict with sub shot suffix as key and None as value.
        subshot_sets = self.reset_subshot_sets(slave_shots)
        # Stop the process if no slave shot found.
        if not slave_shots:
            return subshot_sets
        # Per slave shot found, get the suffix and search for a set with good name.
        for slave_shot in slave_shots:
            suffix = re.findall(r"^sq\d{4}_sh\d{4}(\w$)", slave_shot)[0]
            subshot_set = self.get_target_subshot_set(shot_code, suffix)
            if subshot_set:
                # If found, add it to the dict.
                subshot_sets[suffix] = subshot_set
        return subshot_sets

    def reset_subshot_sets(self, slave_shots):
        """
        Create a dict with sub shot suffix as key and None as value.
        :param slave_shots: slave shot names
        :type slave_shots: list[str]
        :returns: existing sub shot sets. (ie: {'B': None, 'C': None})
        :rtype: dict
        """
        latest_sets = {re.findall(r"^sq\d{4}_sh\d{4}(\w$)", x)[0]: None for x in slave_shots if slave_shots}
        return latest_sets

    def get_target_subshot_set(self, shot_code, targeted_subshot):
        """
        Get the sub shot set linked to the given sub shot suffix.
        :param shot_code: name of the shot
        :type shot_code: str
        :param targeted_subshot: suffix of the sub shot
        :type targeted_subshot: str
        :returns: subshot set name
        :rtype: str
        """
        is_subshot = re.match(r"^sq\d{4}_sh\d{4}\w$", str(shot_code))
        if is_subshot:
            name = "{}_{}".format(shot_code[:-1], targeted_subshot)
        else:
            name = "{}_{}".format(shot_code, targeted_subshot)
        subshot_set = cmds.ls(name, type='objectSet')
        if not subshot_set:
            return
        return subshot_set[0]

    def set_from_selection(self, shot_code, targeted_subshot):
        """
        Get the subshot set linked to the given subshot suffix.
        :param shot_code: name of the shot
        :type shot_code: str
        :param targeted_subshot: suffix of the subshot
        :type targeted_subshot: str
        :returns: subshot set name
        :rtype: str
        """
        # Check the content of the selection and get the targeted set.
        self.check_and_fix_selection()
        targeted_set = self.get_target_subshot_set(shot_code, targeted_subshot)
        if targeted_set:
            # If the subshot set exists, delete it.
            cmds.delete(targeted_set)
        else:
            # If the subshot set does not exist, build the name of the set.
            targeted_set = "{}_{}".format(shot_code, targeted_subshot)
        return cmds.sets(name=targeted_set)

    def check_and_fix_selection(self):
        """
        Check and correct the current selection to set it as a subshot set.
        :returns: new selection with top node names.
        :rtype: set[str]
        """
        # Get the current selection.
        current_sel = cmds.ls(sl=True)
        message = ""
        if not current_sel:
            message += "No selection found.\n"
            self.custom_raise(message)
        # Check if the selection has objectSets and stop the process if there are.
        object_set = [element for element in current_sel if cmds.objectType(element, isType="objectSet")]
        if object_set:
            message += "Sets are not accepted: '{}'.\n".format(", ".join(object_set))
            current_sel = [selected for selected in current_sel if selected not in object_set]
        # Check if the selection has audios and stop the process if there are.
        object_audio = [element for element in current_sel if cmds.objectType(element, isType="audio")]
        if object_audio:
            message += "Audios are not accepted: '{}'.\n".format(', '.join(object_audio))
            current_sel = [selected for selected in current_sel if selected not in object_audio]
        # Rebuild a selection with the top node of each component of the current selection.
        parent_sel = self.get_top_nodes_from_list(current_sel)
        non_dag_nodes = self.get_non_dag_nodes_on_selection(parent_sel)
        if non_dag_nodes:
            message += "Non dag objects found: '{}'.\n".format(", ".join(non_dag_nodes))
            parent_sel = [selected for selected in current_sel if selected not in non_dag_nodes]
        # Do not accept duplicated elements on sub shot sets.
        has_duplicated = self.check_duplicated_on_sets(parent_sel)
        if has_duplicated:
            message += "Duplicated on sets found: '{}'.\n".format(', '.join(has_duplicated))
            parent_sel = [selected for selected in current_sel if selected not in has_duplicated]
        # Do not accept assemblies.
        has_assemblies = self.check_has_assemblies(parent_sel)
        if has_assemblies:
            message += "Assemblies are not accepted.\n"
            parent_sel = [selected for selected in current_sel if selected not in has_assemblies]
        # Do not accept extra assemblies.
        black_listed = self.check_has_common_elements(parent_sel)
        if black_listed:
            message += "Common elements or cams are not accepted.\n"
            parent_sel = [selected for selected in current_sel if selected not in black_listed]
        if message:
            message += "Those elements have been removed from your selection before being added to the set."
            cmds.confirmDialog(title="Selection report", message=message, button=["Close"], icon="error",
                               defaultButton="Close", cancelButton="Close")
        cmds.select(parent_sel)
        return parent_sel

    def get_top_nodes_from_list(self, components):
        """
        Get the top node of each component of a list.
        :param components: elements in the scene
        :type components: list or tuple or set
        :returns: top node names
        :rtype: set
        """
        parent_sel = set()
        for component in components:
            # While a component has a parent, continue the research.
            top_node = self.get_top_node_from_element(component)
            parent_sel.add(top_node)
        return parent_sel

    def get_top_node_from_element(self, component):
        """
        Get the top node of the given component if there is.
        :param component: element in the scene
        :type component: str or unicode
        :returns: top node name
        :rtype: str
        """
        # While a component has a parent, continue the research.
        while True:
            top_node = cmds.listRelatives(component, parent=True)
            if not top_node:
                # When no parent found, add the component inside the list.
                return component
            component = top_node[0]

    def get_non_dag_nodes_on_selection(self, components):
        """
        Check if there are non dag nodes and return them.
        :param components: elements in the scene
        :type components: list or tuple or set
        """
        non_dag_nodes = list()
        dag_objects = cmds.ls(assemblies=True)
        for component in components:
            if component not in dag_objects:
                non_dag_nodes.append(component)
        if non_dag_nodes:
            return non_dag_nodes

    def check_duplicated_on_sets(self, components, subshot_sets=None):
        """
        Get assemblies and check if the current has it.
        :param components: elements in the scene
        :type components: list or tuple or set
        :param subshot_sets: existing sub shot sets
        :type subshot_sets: list
        :returns: duplicated nodes
        :rtype: list
        """
        # Create a list to store duplicated elements inside.
        duplicated = list()
        # Get the sub shot sets.
        if not subshot_sets:
            shot_code = self.engine.context.entity["name"]
            subshot_sets = self.get_subshot_sets(shot_code)
        if not subshot_sets:
            return duplicated
        # Get the content for each set.
        for subshot_set in subshot_sets:
            set_members = cmds.sets(subshot_set, q=True)
            if not set_members:
                continue
            # Check if the element is on other set and store it inside the list.
            for set_member in set_members:
                if set_member in components:
                    duplicated.append(set_member)
        return duplicated

    def check_has_assemblies(self, components):
        """
        Get assemblies and check if the components has them.
        :param components: elements in the scene
        :type components: list or tuple or set or unicode
        :returns: assembly nodes
        :rtype: list
        """
        if isinstance(components, (str, unicode)):
            components = [components]
        # Get assemblies in the scene.
        assemblies = assembly_tools.get_scene_assemblies()
        if not assemblies:
            return
        # Get assembly names.
        assembly_ref_nodes = [str(assembly.refNode) for assembly in assemblies]
        top_nodes = list()
        for assembly in assembly_ref_nodes:
            # For each reference node, get their children top nodes.
            nodes = cmds.referenceQuery(assembly, nodes=True)
            top_nodes.extend(cmds.ls(nodes, assemblies=True))
        # Compare top nodes from reference with assembly top nodes.
        bad_nodes = [top_node for top_node in top_nodes if top_node in components]
        return bad_nodes

    def check_has_common_elements(self, nodes_list):
        """
        Get extra specific assemblies and check if the components has them.
        :param nodes_list: elements in the scene
        :type nodes_list: list or tuple or set or unicode
        :returns: assembly nodes
        :rtype: list
        """
        common_elements = ["trash_grp", "layLights_all_grp", "focusVis_grp", "cycloLay_msh", "animBot"]
        common_elements.extend(self.get_top_node_cameras())
        if isinstance(nodes_list, (str, unicode)):
            nodes_list = [nodes_list]
        nodes_in_common_elements = [element for element in common_elements if element in nodes_list]
        return nodes_in_common_elements

    def add_to_set(self, targeted_subshot, shot_code):
        """
        Add the current selection to the given subshot set.
        :param targeted_subshot: suffix of the subshot
        :type targeted_subshot: str
        :param shot_code: name of the shot
        :type shot_code: str
        :returns: modified set name
        :rtype: str
        """
        # Check the content of the selection and get the targeted set.
        targeted_set = self.get_target_subshot_set(shot_code, targeted_subshot)
        if not targeted_set:
            message = "No pipelined set created.\nPlease create one at least before using this feature."
            self.custom_raise(message)
        self.check_and_fix_selection()
        # Add the selection to the given set.
        cmds.sets(include=targeted_set, noWarnings=True)
        return targeted_set

    def remove_to_set(self, targeted_subshot, shot_code):
        """
        Remove the current selection from the given subshot set.
        :param targeted_subshot: suffix of the subshot
        :type targeted_subshot: str
        :param shot_code: name of the shot
        :type shot_code: str
        :returns: modified set name
        :rtype: str
        """
        # Get the targeted set.
        targeted_set = self.get_target_subshot_set(shot_code, targeted_subshot)
        if not targeted_set:
            message = "No pipelined set created.\nPlease create one at least before using this feature."
            self.custom_raise(message)
        # Remove the selection from the given set.
        cmds.sets(rm=targeted_set)
        return targeted_set

    def check_subshot_content(self, subshot_sets):
        """
        Fix the content of subshot sets.
        :param subshot_sets: sub shot names and their set names
        :type subshot_sets: dict
        """
        shot_code = self.engine.context.entity["name"]
        # Prepare variables to build a correct report.
        all_components = list()
        report = {"state": True, "data": dict(), "message": None}
        message = str()
        for subshot, subshot_set in subshot_sets.items():
            # Prepare lower keys to build a correct report.
            data = {"remove": [], "add": []}
            message += "{}_{}:\n".format(shot_code, subshot)
            has_set = None
            if subshot_set:
                has_set = cmds.objExists(subshot_set)
            if subshot_set is None or not has_set:
                report["state"] = False
                message += "Set does not exist.\n\n"
                continue
            # Get components of the current sub shot.
            components = cmds.sets(subshot_set, query=True)
            if not components:
                report["state"] = False
                message += "Set is empty, it needs to be filled.\n\n".format(subshot_set)
                continue
            for component in components:
                # Check if there are sets.
                is_set = cmds.objectType(component, isType="objectSet")
                if is_set:
                    report["state"] = False
                    data["remove"].append(component)
                    message += "Set object found '{}'.\n".format(component)
                # Check if there are audios.
                is_audio = cmds.objectType(component, isType="audio")
                if is_audio:
                    report["state"] = False
                    data["remove"].append(component)
                    message += "Audio object found '{}'.\n".format(component)
                # Check if there are non-top dag nodes.
                is_non_dag_node = self.get_non_top_dag_nodes(component)
                if is_non_dag_node:
                    report["state"] = False
                    top_node = self.get_top_node_from_element(component)
                    all_components.append(top_node)
                    data["add"].append(top_node)
                    data["remove"].append(component)
                    message += "Non top dag node: '{}'.\n".format(component)
                # Check if there are assembly nodes.
                is_assembly = self.check_has_assemblies(component)
                if is_assembly:
                    report["state"] = False
                    data["remove"].append(component)
                    message += "Is an assembly: '{}'.\n".format(component)
                # Check if there are extra assembly nodes.
                black_listed = self.check_has_common_elements(component)
                if black_listed:
                    report["state"] = False
                    data["remove"].append(component)
                    message += "Is an extra assembly or camera: '{}'.\n".format(component)
            # Check if there are something to report on this sub shot or not.
            if not any([data["remove"], data["add"]]):
                message += "Everything is okay.\n"
            report["data"].update({subshot_set: data})
            message += "\n"
            # Merge component from sub shots into a single list to compare them.
            all_components.extend(components)
        message += "Duplicated on sets: (no fix)\n"
        # If there are elements on multiple sets, report them.
        counts = {i: all_components.count(i) for i in all_components}
        duplicated = list()
        for element, number in counts.items():
            if number > 1:
                report["state"] = False
                duplicated.append(element)
                message += "{}\n".format(element)
        report["data"].update({"duplicated": duplicated})
        if not duplicated:
            message += "Everything is okay.\n"
        # If there are missing assemblies on sets, report them.
        message += "\nMissing top nodes: (no fix)\n"
        missing_assemblies = self.check_missing_assemblies(all_components)
        if missing_assemblies:
            report["state"] = False
            report["data"].update({"missing": missing_assemblies})
            for element in missing_assemblies:
                message += "{}\n".format(element)
        if report["state"]:
            message = "Congrats.\n\nEverything is okay.\nReady to build the sub shots.\n"
        report["message"] = message
        return report

    def fix_subshot_content(self, check_report):
        """
        Fix the content of sub shot sets.
        :param check_report: result of the check function linked
        :type check_report: dict
        """
        no_fix = False
        data = check_report.get("data")
        # For each element on the report, auto fix it depends on the keyword.
        for subshot_set, action in data.items():
            if subshot_set in ["duplicated", "missing"]:
                if data[subshot_set]:
                    no_fix = True
                continue
            if action.get("add"):
                # Add on set.
                cmds.select(action.get("add"), ne=True)
                cmds.sets(include=subshot_set, noWarnings=True)
            if action.get("remove"):
                # Remove from set.
                cmds.select(action.get("remove"), ne=True)
                cmds.sets(rm=subshot_set)
        if not no_fix:
            check_report["state"] = True
        return check_report

    def check_missing_assemblies(self, set_components):
        """
        Check if there are missing top nodes inside the content result of all sub shot sets.
        :param set_components: content of all sub shot sets
        :type set_components: list
        :returns: missing elements between set components and all top nodes.
        :rtype: list
        """
        missing_elements = list()
        top_nodes = cmds.ls(assemblies=True)
        black_list = ["trash_grp", "layLights_all_grp", "focusVis_grp", "cycloLay_msh"]
        top_cams = self.get_top_node_cameras()
        assemblies = self.check_has_assemblies(top_nodes)
        top_nodes = [top_node for top_node in top_nodes if top_node not in top_cams and not top_node in assemblies]
        top_nodes = [top_node for top_node in top_nodes if top_node not in black_list]
        for node in top_nodes:
            if node not in set_components:
                missing_elements.append(node)
        return missing_elements

    def get_top_node_cameras(self):
        """
        List all the top nodes that contains cameras as child.
        :returns: top nodes cameras
        :rtype: list
        """
        cams = cmds.listCameras()
        top_cams = list()
        for cam in cams:
            is_non_dag_node = self.get_non_top_dag_nodes(cam)
            if is_non_dag_node:
                top_node = self.get_top_node_from_element(cam)
                top_cams.append(top_node)
            else:
                top_cams.append(cam)
        return top_cams

    def get_subshot_sets(self, shot_code=None):
        """
        Get sub shot sets in the scene from the current scene context.
        :param shot_code: shot name
        :type shot_code: str
        :returns: the sub shot sets
        :rtype: list
        """
        if not shot_code:
            context = self.engine.context
            shot_code = context.entity["name"]
        is_subshot = re.match(r"^sq\d{4}_sh\d{4}\w$", str(shot_code))
        if is_subshot:
            name = r"{}_*".format(shot_code[:-1])
        else:
            name = r"{}_*".format(shot_code)
        # Filter sets components that starts with the shot name.
        filter_sets = cmds.ls(name, type='objectSet')
        # Filter sets that match the naming convention of the sub shot sets.
        filter_matches = [element for element in filter_sets if re.match(r"^sq\d{4}_sh\d{4}_\w$", element)]
        return filter_matches

    def get_subshot_variant(self, shot_code=None):
        """
        Get the variant letter of the shot from the shot name.
        :param shot_code: shot name
        :type shot_code: str
        :returns: the variant letter
        :rtype: str
        """
        if not shot_code:
            context = self.engine.context
            shot_code = context.entity["name"]
        subshot_variants = re.findall(r"^sq\d{4}_sh\d{4}(\w)$", shot_code)
        if subshot_variants:
            return subshot_variants[0]
        return

    def get_subshot_set_variant(self, targeted_set):
        """
        Get the variant letter of the sub shot set from the shot name.
        :param targeted_set: sub shot set name
        :type targeted_set: str
        :returns: the variant letter
        :rtype: str
        """
        subshot_variant = re.findall(r"^sq\d{4}_sh\d{4}_(\w)$", targeted_set)
        if subshot_variant:
            return subshot_variant[0]
        return

    def get_subshot_set_variants(self, subshot_sets, shot_code=None):
        """
        Get the variant letter of the sub shot sets from the shot name.
        :param subshot_sets: sub shot names
        :type subshot_sets: list
        :param shot_code: shot name
        :type shot_code: str
        """
        if not shot_code:
            context = self.engine.context
            shot_code = context.entity["name"]
        sorted_subshot_sets = dict()
        is_subshot = re.match(r"^sq\d{4}_sh\d{4}\w$", str(shot_code))
        if is_subshot:
            shot_code = shot_code[:-1]
        # Build a dict with variant letter and its set name linked.
        for subshot_set in subshot_sets:
            set_variants = re.findall(r"^{}_(\w$)".format(shot_code), str(subshot_set))
            if set_variants:
                sorted_subshot_sets[set_variants[0]] = subshot_set
        return sorted_subshot_sets

    def get_top_reference_nodes_from_list(self, components):
        """
        Get the top node of each component of a list.
        :param components: components
        :type components: list or tuple or set
        :returns: top node names
        :rtype: set
        """
        new_list = set()
        # Return a list with all top references nodes linked to the given components.
        for component in components:
            top_reference_node = self.get_top_reference_node(component)
            if not top_reference_node:
                continue
            new_list.add(top_reference_node)
        return new_list

    def get_top_reference_node(self, component):
        """
        Get the top reference node of the given component if there is.
        :param component: element in the scene
        :type component: str or unicode
        :returns: top node reference name
        :rtype: str
        """
        is_referenced = cmds.referenceQuery(component, isNodeReferenced=True)
        if not is_referenced:
            return
        return cmds.referenceQuery(component, topReference=True, referenceNode=True)

    def get_non_dag_nodes_on_set(self, targeted_set):
        """
        Check if there are non dag nodes and raise them if there are.
        :param targeted_set: sub shot set name
        :type targeted_set: str
        """
        non_dag_nodes = list()
        dag_objects = cmds.ls(assemblies=True)
        set_members = cmds.sets(targeted_set, q=True)
        for set_member in set_members:
            if set_member not in dag_objects:
                non_dag_nodes.append(set_member)
        if non_dag_nodes:
            return non_dag_nodes

    def get_non_top_dag_nodes(self, component):
        """
        Check if the component is a non dag node or not. Return True when it is a non dag node.
        :param component: element in the scene
        :type component: str
        """
        dag_objects = cmds.ls(assemblies=True)
        if component not in dag_objects:
            return True
        return False

    def select_set_members(self, targeted_set):
        """
        Select the components of the targeted sub shot set.
        :param targeted_set: sub shot set name
        :type targeted_set: str
        """
        set_members = cmds.sets(targeted_set, q=True)
        cmds.select(set_members)

    def custom_raise(self, message):
        """
        Create a basic maya popup message and show it.
        :param message: message to log
        :type message: str
        """
        self.show_popup_dialog(message)
        cmds.error(message)

    def show_popup_dialog(self, message, title="Error", icon="error"):
        """
        Create a basic maya popup message and show it.
        :param message: message to show in the popup window
        :type message: str
        :param title: message to show in the popup window
        :type title: str
        :param icon: logo to show in the window (ie: information, warning, error, critical)
        :type icon: str
        """
        default = "Close"
        cmds.confirmDialog(title=title, message=message, button=[default], icon=icon,
                           defaultButton=default, cancelButton=default)

    def get_parent_shots(self, shot_code=None):
        """
        Get the parent shot info depending on the shot.
        :param shot_code: name of the shot
        :type shot_code: str
        :returns: slave shot names
        :rtype: list[str]
        """
        # Query the shot info from the shot name.
        context = self.engine.context
        if not shot_code:
            shot_code = context.entity["name"]
        parent_shot_field = "parent_shots"
        sg_filters = [
            ["project", "is", context.project],
            ["code", "is", shot_code],
            ["sg_status_list", "is_not", "omit"]]
        data_shot = self.engine.shotgun.find("Shot", filters=sg_filters, fields=[parent_shot_field])
        if not data_shot:
            cmds.error("No parent shot found.\nPlease verify the shot info on Shotgrid.")
        # Get the name of the slave shots.
        parent_shots = [slave.get("name") for slave in data_shot[0][parent_shot_field]]
        return parent_shots

    def manage_set_content(self, shot_code=None):
        """
        Increase the instance number of sub shot set members depending on the suffix on the set name.
        :param shot_code: name of the shot
        :type shot_code: str
        """
        # Define a base number for the instance depending on the variant sub shot.
        rules = {"B": 100, "C": 200, "D": 300, "E": 400, "F": 500, "G": 600, "H": 700, "I": 800, "J": 900}
        if not shot_code:
            context = self.engine.context
            shot_code = context.entity["name"]
        # Get the variant of the shot and his linked sub shot set.
        subshot_variant = self.get_subshot_variant(shot_code)
        if not subshot_variant:
            cmds.error("Not in sub shot context: {}".format(shot_code))
        targeted_set = self.get_target_subshot_set(shot_code, subshot_variant)
        set_variant = self.get_subshot_set_variant(targeted_set)
        if not set_variant:
            cmds.error("Bad naming convention for the given set: {}".format(targeted_set))
        if subshot_variant != set_variant:
            cmds.error("Scene variant and sub shot set variant do not match together.")
        # Get the corresponding base instance number.
        instance_update = rules.get(subshot_variant)
        set_members = cmds.sets(targeted_set, q=True)
        set_members.sort()
        # Sort asset by names and upgrade their instance number.
        assets_filtered = self.sort_by_asset_name(set_members)
        self.increase_instance_number(assets_filtered, instance_update)
        cmds.delete(targeted_set)

    def sort_by_asset_name(self, set_members):
        """
        Sort a list by asset names based on an underscore name split.
        :param set_members: list of component
        :type set_members: list or tuple or set
        :returns: results by asset name (ie: {"ChickA": ["ch_ChickA_rig_001RN", "ch_ChickA_rig_001:all_grp"]})
        :rtype: dict
        """
        # Build a dict by asset names as key and matching components as values.
        assets_filtered = dict()
        for set_member in set_members:
            # Get the asset name by using the common naming convention.
            split_name = set_member.split("_")
            matches = list()
            # Add a flexibility to avoid index error by splitting the name.
            if len(split_name) > 1:
                asset_name = split_name[1]
            else:
                asset_name = split_name[0]
            for y in set_members:
                # If the name split matches is on the asset, then keep it.
                if asset_name in y:
                    matches.append(y)
            if matches:
                assets_filtered.update({asset_name: matches})
        return assets_filtered

    def increase_instance_number(self, assets_filtered, instance_update):
        """
        Increase the instance number by the given base number and rename the component with their namespaces.
        :param assets_filtered: components filtered by asset name
        :type assets_filtered: dict
        :param instance_update: base number to iterate instance numbers
        :type instance_update: int
        """
        # Need a dict like this: (ie: {"ChickA": ["ch_ChickA_rig_001RN", "ch_ChickA_rig_001:all_grp"]})
        reference_nodes = set()
        for name, members in assets_filtered.items():
            # The count will be used to iterate the instance number added to the base instance number of the variant.
            count = 1
            for member in members:
                logging.info("Renaming the element: '{}'.".format(member))
                is_proxy = bool(re.match(r"proxy_\w+_\d{3}_.*", member))
                # Keep three string groups from the name: before/after instance number of the first namespace, suffix.
                while not is_proxy:
                    name_parts = re.findall(r"(\w+_)\d{3}(_\w*)?(:.+)?$", member)
                    new_instance_number = str(instance_update + count)
                    if name_parts:
                        name_parts = name_parts[0]
                        if len(name_parts) >= 3:
                            new_name = "{}{}".format(name_parts[0], new_instance_number, name_parts[1])
                        else:
                            new_name = "{}{}".format(name_parts[0], new_instance_number)
                    else:
                        # Or copy the full name of the member if no match with the expected naming convention.
                        if member.endswith("_"):
                            member = member[:-1]
                        new_name = "{}_{}".format(member, new_instance_number)
                    # Add a security to know if the name or namespace still exist, if yes, add an interation.
                    obj_exists = cmds.objExists(new_name)
                    namespace_exists = cmds.namespace(exists=new_name)
                    conditions = any((obj_exists, namespace_exists))
                    if conditions:
                        count += 1
                        logging.warning("Object or namespace '{}' exists. Upgrade instance number.".format(new_name))
                    else:
                        break
                # Check if the member is or has a reference node to change his namespace and rename it.
                reference_node = None
                is_reference = cmds.objectType(member, isType="reference")
                has_reference = self.get_top_reference_node(member)
                if is_reference:
                    reference_node = member
                elif has_reference:
                    reference_node = has_reference
                elif is_proxy:
                    logging.info("The component '{}' is a proxy. Will be replaced by a published asset.".format(member))
                    do_switch = self.switch_proxy_to_asset(member, instance_update)
                    if not do_switch:
                        logging.warning("Cannot find assets on SG from the proxy name. Pass.")
                else:
                    cmds.rename(member, new_name)
                # In case of a reference has multiple top nodes, we don't want to iterate on the same reference node.
                if reference_node and reference_node not in reference_nodes:
                    reference_nodes.add(reference_node)
                    # Unlock the reference node to rename it and lock it back.
                    cmds.lockNode(reference_node, lock=False)
                    # Get the file from the reference node to rename the namespace of this file.
                    file_name = cmds.referenceQuery(reference_node, f=True)
                    cmds.file(file_name, edit=True, namespace=new_name)
                    if new_name.endswith("RN"):
                        cmds.rename(reference_node, new_name)
                    elif not new_name.endswith("RN"):
                        new_name = "{}RN".format(new_name)
                        cmds.rename(reference_node, new_name)
                    cmds.lockNode(new_name, lock=True)
                count += 1

    def switch_proxy_to_asset(self, proxy_name, instance_update):
        """
        Get the asset name from proxy element inside
        :param proxy_name: name of the proxy element name like this: proxy_name_001(+ suffix accepted)
        :type proxy_name: str
        :param instance_update: base number to iterate instance numbers
        :type instance_update: int
        :returns: reference node found and loaded
        :rtype: bool
        """
        asset_name_parts = proxy_name.split("_")
        if not len(asset_name_parts) > 2:
            logging.warning("Proxy does not have a good naming convention, pass it.")
            return False
        asset_name = asset_name_parts[1]
        last_published_file = self.get_latest_published_files(asset_name, "entity.Asset.code", "maya_rig_publish_high_file", "rig")
        if not last_published_file:
            return
        asset_path = last_published_file.get("path").get("local_path")
        namespace = self.build_proxy_name(asset_name, asset_path, instance_update)
        try:
            context = self.engine.context
            (b_module, b_class_name) = mglImport.get_module_python_class(
                root_class="Builder",
                root_module="mglMayaScene",
                stage_name="build",
                context=context)
            b = b_class_name()
            ref_file = b.create_reference(asset_path, namespace=namespace)
        except Exception:
            logging.warning("Import failed: '{}'.".format(asset_name))
            return
        # Get the reference node created.
        current_reference = ref_file.refNode.name()
        reference_obj = pymel.core.ls(ref_file.nodes(), assemblies=True)
        referenced_assemblies = [ref.name() for ref in reference_obj]
        if not current_reference:
            logging.warning("No asset found to switch the proxy: {}. Rename it only.".format(proxy_name))
            cmds.rename(proxy_name, namespace)
        self.copy_proxy_anim_to_reference(referenced_assemblies[0], proxy_name)
        cmds.delete(proxy_name)
        cmds.select(referenced_assemblies)
        shot_code = context.entity["name"]
        # Get the variant of the shot and his linked sub shot set.
        subshot_variant = self.get_subshot_variant(shot_code)
        targeted_set = self.get_target_subshot_set(shot_code, subshot_variant)
        cmds.sets(include=targeted_set, noWarnings=True)
        return namespace

    def get_latest_published_files(self, name, entity_type, publish_file_type, task):
        """
        Get latest published files asset from asset name.
        :param name: asset name to import as reference
        :type name: list or tuple or str
        :param entity_type: entity type to get
        :type entity_type: str
        :param publish_file_type: published file type to get
        :type publish_file_type: str
        :param task: task to get the file
        :type task: str
        :returns: asset data
        :rtype: dict
        """
        # Get engine and context.
        context = self.engine.context
        sg_filters = [
            ["project", "is", context.project],
            [entity_type, "is", name],
            ["published_file_type.PublishedFileType.short_name", "is", publish_file_type],
            ["task.Task.content", "is", task],
            ["sg_status_list", "is_not", "omit"]]
        sg_order = [{"field_name": "version_number", "direction": "desc"}]
        # Query the published files of the asset.
        published_files = self.engine.shotgun.find("PublishedFile", filters=sg_filters, fields=['path'], order=sg_order)
        # Stop the research for the current asset at the first result.
        if not published_files:
            logging.warning("No published file found for '{}'.".format(name))
            return
        return published_files[0]

    def build_proxy_name(self, asset_name, asset_path, instance_update):
        """
        Build the proxy name following the shot_namespace template.
        :param asset_name: asset name to import as reference
        :type asset_path: list or tuple or str
        :param asset_path: asset path to import as reference
        :type asset_name: str
        :type instance_update: int
        :returns: reference node found and loaded
        """
        # Get the shot_namespace template to build the namespace.
        namespace_template = self.engine.sgtk.templates["shot_namespace"]
        alembic_template = self.engine.sgtk.template_from_path(asset_path)
        pf_fields = alembic_template.get_fields(asset_path)
        pf_fields['extra_info'] = pf_fields.get("Task")
        name_start = "_".join((pf_fields["short_asset_type"], asset_name, pf_fields["extra_info"]))
        equivalents = cmds.ls("{}_*".format(name_start))
        equivalents.sort()

        # Upgrade the instance number.
        if equivalents:
            int_iteration = 1
            last_iteration = re.findall(name_start + r"_(\d{3})(?:_?\w*)", equivalents[-1])
            if last_iteration:
                int_iteration = int(last_iteration[0])
            else:
                logging.warning("Not expected name from proxy equivalent '{}', set its instance number as '001'.")
            if int_iteration > instance_update:
                new_iteration = int_iteration + 1
            else:
                new_iteration = instance_update + int_iteration + 1
        else:
            new_iteration = instance_update + 1
        pf_fields['iteration_number'] = new_iteration
        # Build the namespace.
        namespace = namespace_template.apply_fields(pf_fields).replace("-", "_")
        return namespace

    def copy_proxy_anim_to_reference(self, ref_assembly, proxy_name):
        """
        Paste the proxy's matrix to the world controller of each referenced assemblies.
        :param ref_assembly: name of the referenced assembly: proxy_ChickMutantA001_001(+ suffix accepted)
        :type ref_assembly: str
        :param proxy_name: name of the proxy element name like this: proxy_name_001(+ suffix accepted)
        :type proxy_name: str
        """
        # Get info from world/global/local controllers from NOD rigs.
        ref_namespace = ref_assembly.split(":")[0]
        world_ctl_name = "{}:world_C0_ctl".format(ref_namespace)
        global_ctl_name = "{}:global_C0_ctl".format(ref_namespace)
        local_ctl_name = "{}:local_C0_ctl".format(ref_namespace)
        scale_attr_name = "global_scale"
        # Get info from god/base controllers from ATL rigs.
        god_ctl_name = "{}:m_god_ctl_01".format(ref_namespace)
        base_ctl_name = "{}:m_base_ctl_01".format(ref_namespace)
        has_assembly_world_ctl = cmds.objExists(world_ctl_name)
        has_assembly_global_ctl = cmds.objExists(global_ctl_name)
        has_assembly_local_ctl = cmds.objExists(local_ctl_name)
        has_assembly_god_ctl = cmds.objExists(god_ctl_name)
        has_assembly_base_ctl = cmds.objExists(base_ctl_name)
        has_scale_attr = None
        # This attribute is unique on global controllers, it is a float attribute for uniformed scale.
        if has_assembly_world_ctl:
            has_scale_attr = cmds.attributeQuery(scale_attr_name, node=world_ctl_name, exists=True)
        if not any((has_assembly_world_ctl, has_assembly_global_ctl, has_assembly_local_ctl, god_ctl_name, base_ctl_name)):
            logging.error("The element '{}' is not prevent to be animated properly. Pass.".format(ref_namespace))
            return
        try:
            proxy_controllers_shape = cmds.listRelatives(proxy_name, ad=True, ni=True, type="nurbsCurve")
            proxy_controllers = list()
            for ctl in proxy_controllers_shape:
                proxy_controllers.append(cmds.listRelatives(ctl, parent=True)[0])
        except (TypeError, ValueError):
            logging.error("No children found inside '{}'. Pass.".format(proxy_name))
            return
        for count, ctl in enumerate(proxy_controllers):
            # Count is used to do 3 loops max, and to control the order to copy animations.
            if count == 0:
                # Firstly, we copy animation from parent to world or god controller.
                has_keys = bool(cmds.findKeyframe(ctl, curve=True, animation="objects", at=['translate', 'rotate']))
                if has_assembly_world_ctl and has_scale_attr:
                    # By default, we parent the controller to get the same base and avoid attrib without keys.
                    constraint = cmds.parentConstraint(ctl, world_ctl_name)
                    cmds.delete(constraint)
                    if has_keys:
                        # If the controller has animation keys, copy the animation.
                        cmds.copyKey(ctl, at=["translate", "rotate"], option="curve", animation="objects")
                        cmds.pasteKey(world_ctl_name, animation="objects", o="replaceCompletely")
                    has_scale_keys = bool(cmds.findKeyframe(ctl, curve=True, animation="objects", at="scaleX"))
                    if has_scale_keys:
                        # We consider the scale as uniform on this prod, we copy the X axis to the given attribute.
                        cmds.copyKey(ctl, at=["scaleX"], option="curve", animation="objects")
                        cmds.pasteKey(world_ctl_name, animation="objects", o="replaceCompletely", at=scale_attr_name)
                    else:
                        # Scale parent if no key, to match the scale base.
                        proxy_uniform_scale = cmds.getAttr("{}.scaleX".format(ctl))
                        cmds.setAttr("{}.{}".format(world_ctl_name, scale_attr_name), proxy_uniform_scale)
                elif has_assembly_god_ctl:
                    # Copy animations.
                    self.copy_matrix_and_anim(ctl, god_ctl_name, has_keys, copy_scale=True)
            elif count == 1:
                # Secondly, we copy animation from sub parent to global or base controller.
                has_keys = bool(cmds.findKeyframe(ctl, curve=True, animation="objects", at=["translate", "rotate"]))
                if has_assembly_world_ctl and has_assembly_global_ctl:
                    self.copy_matrix_and_anim(ctl, global_ctl_name, has_keys)
                elif has_assembly_god_ctl and has_assembly_base_ctl:
                    self.copy_matrix_and_anim(ctl, base_ctl_name, has_keys)
            elif count == 2:
                # Then we do the same for the local one.
                has_keys = bool(cmds.findKeyframe(ctl, curve=True, animation="objects", at=["translate", "rotate"]))
                if has_assembly_world_ctl and has_assembly_global_ctl and has_assembly_local_ctl:
                    self.copy_matrix_and_anim(ctl, local_ctl_name, has_keys)
                break

    def copy_matrix_and_anim(self, parent, target, has_keys, copy_scale=False, scale_attr="scale"):
        """
        Constraint the target to the parent, delete the constraint and copy/paste the animation curves on the target.
        :param parent: parent object name to get matrix
        :type parent: str
        :param target: target object name to get matrix
        :type target: str
        :param has_keys: has keys or not on parent attributes
        :type has_keys: bool
        :param copy_scale: allow to copy/paste scale attribute from the parent to the target
        :type copy_scale: bool
        :param scale_attr:
        :type scale_attr: str
        """
        # Parent the target to the parent once.
        constraint = cmds.parentConstraint(parent, target)
        cmds.delete(constraint)
        # Copy animation if there are.
        if has_keys:
            cmds.copyKey(parent, at=["translate", "rotate"], option="curve", animation="objects")
            cmds.pasteKey(target, animation="objects", o="replaceCompletely")
        if not copy_scale:
            return
        has_scale_keys = cmds.findKeyframe(parent, curve=True, animation="objects", at=scale_attr)
        if has_scale_keys:
            cmds.copyKey(parent, at=scale_attr, option="curve", animation="objects")
            cmds.pasteKey(target, animation="objects", o="replaceCompletely", at=scale_attr)
        else:
            proxy_scale = cmds.getAttr("{}.{}".format(parent, scale_attr))
            cmds.setAttr("{}.{}".format(target, scale_attr), proxy_scale)
