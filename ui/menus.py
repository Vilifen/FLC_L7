class MenuBuilder:
    def __init__(self, window, actions):
        self.window = window
        self.actions = actions

        menubar = window.menuBar()

        self.file_menu = menubar.addMenu(window.labels["file"])
        self.file_menu.addAction(actions.menu_new)
        self.file_menu.addAction(actions.menu_open)
        self.file_menu.addAction(actions.menu_save)
        self.file_menu.addAction(actions.menu_save_as)
        self.file_menu.addSeparator()
        self.file_menu.addAction(actions.menu_exit)

        self.edit_menu = menubar.addMenu(window.labels["edit"])
        self.edit_menu.addAction(actions.menu_undo)
        self.edit_menu.addAction(actions.menu_redo)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(actions.menu_cut)
        self.edit_menu.addAction(actions.menu_copy)
        self.edit_menu.addAction(actions.menu_paste)
        self.edit_menu.addAction(actions.menu_delete)
        self.edit_menu.addSeparator()
        self.edit_menu.addAction(actions.menu_select_all)

        self.text_menu = menubar.addMenu(window.labels["text"])
        self.text_menu.addAction(actions.menu_text_task)
        self.text_menu.addAction(actions.menu_text_grammar)
        self.text_menu.addAction(actions.menu_text_class)
        self.text_menu.addAction(actions.menu_text_method)
        self.text_menu.addAction(actions.menu_text_example)
        self.text_menu.addAction(actions.menu_text_literature)
        self.text_menu.addAction(actions.menu_text_source)

        self.run_menu = menubar.addMenu(window.labels["run"])
        self.run_menu.addAction(actions.menu_run)

        self.help_menu = menubar.addMenu(window.labels["help"])
        self.help_menu.addAction(actions.menu_help)
        self.help_menu.addAction(actions.menu_about)

        self.localization_menu = menubar.addMenu(window.labels["localization"])
        self.localization_menu.addAction(actions.lang_ru)
        self.localization_menu.addAction(actions.lang_en)

        self.view_menu = menubar.addMenu(window.labels["view"])

        self.ast_menu = menubar.addMenu("AST")
        self.ast_menu.addAction(actions.menu_ast_text)
        self.ast_menu.addAction(actions.menu_ast_visual)

    def update_menu_titles(self):
        L = self.window.labels
        self.file_menu.setTitle(L["file"])
        self.edit_menu.setTitle(L["edit"])
        self.text_menu.setTitle(L["text"])
        self.run_menu.setTitle(L["run"])
        self.help_menu.setTitle(L["help"])
        self.localization_menu.setTitle(L["localization"])
        self.view_menu.setTitle(L["view"])