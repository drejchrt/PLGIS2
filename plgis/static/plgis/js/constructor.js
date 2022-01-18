function generate_traverse_inputs(i){ //i => Traverse number
    return $(`
        <div class="row mb-1">
            <div class="col-6 text-left">
                Traverse ${String(i).padStart(2,'0')}
            </div> 
            <div class="col-6 text-right">
                <button class="btn btn-primary" type="button" data-toggle="modal" data-target="#modal-t-${i}">
                    <i class="fa fa-plus"></i> Add Bundle                    
                </button>
            </div>
        </div>
        <div class="row" id="t-${i}-chips">
        </div>
    `)
}

function add_bundle(t){
    var data ={};
    $(`form#form-t-${t} :input`).each(function(){
         data[$(this).attr('name')] = $(this).val();
    })
    var bdnr = `${data["side"]}-${data["position"]}`
    var bundle = {}
    bundle =  {
        "side": data["side"],
        "position": data["position"],
        "components":data["components"],
        "cables": {
            'config':data["config"],
            'count':data["count"]
        }
    }
    // append to json
    for (var tower_name in tree['towers']){
        var to = tree['towers'][tower_name]
        to['traverses']['traverse' + String(t).padStart(2,'0')]['bundles'][bdnr] = bundle;
    }
    // rebuild tree view
    constructTree(tree)

    // add bundle chip
    $(`
        <div class="chip">
          ${bdnr}
          <span class="closebtn" onclick="this.parentElement.style.display='none'">&times;</span>
        </div> 
    `).appendTo(`#t-${t}-chips`)


    $(`#modal-t-${t}`).modal('hide')
}

function generate_bundle_modal(i) { //i => Traverse number
    return $(`
        <div id="modal-t-${i}" class="modal fade bundle-modal">
            <div class="modal-dialog" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Add new Bundle</h5>
                        <button class="close" type="button" data-dismiss="modal" aria-label="Close">
                            <span aria-hidden="true">×</span>
                        </button>
                    </div>
                    <div class="modal-body">
                        <form id="form-t-${i}" class="bundle-form">
                            <div class="row mb-1">
                                <div class="col-6">
                                    <label for="side">Side:</label>
                                    <select name='side' class="form-control">
                                        <option value="L">Left</option>
                                        <option value="M">Middle</option>
                                        <option value="R">Right</option>
                                    </select>
                                </div>
                                <div class="col-6">
                                    <label for="position">Position:</label>
                                    <input name="position" class="form-control" type="number">
                                </div>
                            </div>
                            <div class="dropdown-divider"></div>
                            <div class="row">
                                <label class="col-12">Bundle Components:</label>
                            </div>
                            <div class="row selector mb-1" id="selector-tower-components">
                                <div class="col-6 text-center" id="left">
                                    <span class="selector-subheader bg-dark">Available Components:</span>
                                    <select id="available" multiple>
                                        {# TODO: Get all components via AJAX #}
                                        <option value="Insulator">Insulator</option>
                                        <option value="Fitting">Fitting</option>
                                        <option value="Vibration Dampers">Vibration Dampers</option>
                                        <option value="Marker Balls">Marker Balls</option>
                                    </select>
                                </div>
                                <div class="col-6 text-center" id="right">
                                    <span class="selector-subheader bg-success">Selected Components:</span>
                                    <select name="components" id="selected" multiple>
                                    </select>
                                </div>
                            </div>
                            <div class="dropdown-divider"></div>
                            <div class="row">
                                <div class="col-6">
                                    <label for="count">Number of cables:</label>
                                    <input name="count" class="form-control" type="number">
                                </div>
                                <div class="col-6">
                                    <label for="config">Cable Configuration</label>
                                    <select name='config' class="form-control">
                                        <option data-n="1" value="S">Single</option>
                                        <option data-n="2" value="DH">Double Horizontal</option>
                                        <option data-n="2" value="DV">Double Vertical</option>
                                        <option data-n="3" value="TT">Triple Top</option>
                                        <option data-n="3" value="TB">Triple Bottom</option>
                                        <option data-n="4" value="Q">Quadruple</option>
                                    </select>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer text-right">
                        <button class="btn btn-secondary" data-dismiss="modal">
                            <i class="fa fa-ban"></i> Cancel
                        </button>
                        <button class="btn btn-primary button-bundle" id="add-bundle-t-${i}" onclick="add_bundle(${i})">
                            <i class="fa fa-plus"></i> Add
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `)
}