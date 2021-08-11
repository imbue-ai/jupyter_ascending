// Entry point for the notebook bundle containing custom model definitions.

// debugger;
define(["base/js/namespace"], function (Jupyter) {
    "use strict";

    window["requirejs"].config({
        map: {
            "*": {
                jupyter_ascending: "nbextensions/jupyter_ascending/index",
            },
        },
    });

    const IS_DEBUG = false;
    const TARGET_NAME = "AUTO_SYNC::notebook";

    function get_notebook_name() {
        // return window.document.getElementById("notebook_name").innerHTML;
        return Jupyter.notebook.notebook_path;
    }

    function is_synced_notebook() {
        return get_notebook_name().includes(".sync.ipynb");
    }

    function get_cell_from_notebook(cell_number) {
        let cell = Jupyter.notebook.get_cell(cell_number);

        while (cell === null) {
            // Kind of meh hack to just keep spamming cells at bottom until we get to the cell we want.
            Jupyter.notebook.insert_cell_at_bottom();

            cell = Jupyter.notebook.get_cell(cell_number);
        }

        return cell;
    }

    function update_cell_contents(data) {
        let cell = get_cell_from_notebook(data.cell_number);

        cell.set_text(data.cell_contents);

        // Changed cell types.
        if (cell.cell_type !== data.cell_type) {
            if (data.cell_type === "markdown") {
                Jupyter.notebook.cells_to_markdown([data.cell_number]);
            } else if (data.cell_type === "code") {
                Jupyter.notebook.cells_to_code([data.cell_number]);
            }
        }

        // Markdown cells need a re-render when we update them.
        if (cell.cell_type === "markdown") {
            cell.render();
        }
    }

    function execute_cell_contents(data) {
        let cell = get_cell_from_notebook(data.cell_number);

        cell.focus_cell();
        cell.execute();

        // TODO: ??
        cell.focus_cell();
    }

    function execute_all_cells() {
        Jupyter.notebook.execute_all_cells();
    }

    function op_code__delete_cells(data) {
        console.log("Deleting cell...", data);

        Jupyter.notebook.delete_cells(data.cell_indices);
    }

    function op_code__insert_cell(data) {
        console.log("Inserting cell...", data);

        let new_cell = Jupyter.notebook.insert_cell_at_index(
            data.cell_type,
            data.cell_number
        );
        new_cell.set_text(data.cell_contents);

        // Markdown cells need a re-render when we update them.
        if (new_cell.cell_type === "markdown") {
            new_cell.render();
        }
    }

    function op_code__replace_cell(data) {
        console.log("Replacing cell...", data);

        update_cell_contents(data);
    }

    // function focus_cell(data) {
    //   let cell = get_cell_from_notebook(data.cell_number);

    //   cell.focus_cell();
    //   // TODO: Focus the output so you can see all of it if it's long
    // }

    function get_cells_without_outputs() {
        let cells = Jupyter.notebook.get_cells();
        let cells_cloned = JSON.parse(JSON.stringify(cells));
        for (let cell of cells_cloned) {
            cell.outputs = [];
        }
        return cells_cloned;
    }

    function get_status(comm_obj) {
        comm_obj.send({
            command: "update_status",
            status: get_cells_without_outputs(),
        });
    }

    function start_sync_notebook(comm_obj, msg) {
        comm_obj.send({
            command: "merge_notebooks",
            javascript_cells: get_cells_without_outputs(),
            new_notebook: msg.content.data.cells,
        });
    }

    function create_and_register_comm() {
        // Make sure that the extension is loaded.
        //  TODO: Perhaps it's possible to not do  this if it's already loaded,
        //  but it's fine to be run multiple times.
        //
        //  As a note, I think some people would probably disapprove of this?
        //  It just runs code... but that's what plugins do?
        Jupyter.notebook.kernel.execute("%load_ext jupyter_ascending");

        Jupyter.notebook.kernel.comm_manager.register_target(
            TARGET_NAME,
            // comm is the frontend comm instance
            // msg is the comm_open message, which can carry data
            function (comm, _msg) {
                // Register handlers for later messages:
                comm.on_msg(function (msg) {
                    if (IS_DEBUG) {
                        console.log("Processing a message");
                        console.log(msg);
                    }

                    const data = msg.content.data;
                    const command = data.command;

                    switch (command) {
                        case "start_sync_notebook":
                            console.log("Starting Sync");
                            return start_sync_notebook(comm, msg);
                        case "op_code__delete_cells":
                            return op_code__delete_cells(data);
                        case "op_code__insert_cell":
                            return op_code__insert_cell(data);
                        case "op_code__replace_cell":
                            return op_code__replace_cell(data);
                        case "get_status":
                            console.log("Sending get_status");
                            return get_status(comm);
                        case "update":
                            return update_cell_contents(data);
                        case "execute":
                            return execute_cell_contents(data);
                        case "execute_all":
                            return execute_all_cells();
                        case "status":
                            console.log("give em the status");
                            return;
                        case "restart_kernel":
                            Jupyter.notebook.kernel.restart();
                            return;
                        case "finish_merge":
                            comm.send({command: 'merge_complete'});
                            return;
                        default:
                            console.log("Got an unexpected message: ", msg);
                            return;
                    }
                });

                comm.on_close(function (msg) {
                    console.log("close", msg);
                });
            }
        );
    }

    // Export the required load_ipython_extension function
    return {
        load_ipython_extension: function () {
            Jupyter.notebook.config.loaded
                .then(
                    function on_config_loaded() {
                        console.log("Loaded config...");
                    },
                    function on_config_error() {
                        console.log("ERROR OF LOADING...???");
                    }
                )
                .then(function actually_load() {
                    console.log("===================================");
                    // console.log(ascend);
                    console.log("Loading Jupyter Ascending extension...");
                    console.log("Opening... ", get_notebook_name());
                    console.log("Is synced: ", is_synced_notebook());

                    console.log("Attemping create comm...");
                    if (Jupyter.notebook.kernel) {
                        create_and_register_comm();
                    } else {
                        Jupyter.notebook.events.one(
                            "kernel_ready.Kernel",
                            () => {
                                console.log("We actually reloaded!");
                                create_and_register_comm();
                            }
                        );
                    }
                    Jupyter.notebook.events.on(
                        "kernel_ready.Kernel",
                        () => {
                            console.log("Registering notebook after kernel restart...");
                            Jupyter.notebook.kernel.execute("import jupyter_ascending.extension; jupyter_ascending.extension.set_everything_up()");
                        }
                    );

                    console.log("... success!");

                    console.log("===================================");
                });
        },
    };
});
