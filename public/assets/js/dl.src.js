$(document).ready(function() {
    let onLoading = false;
    let index = 1;
    $("#form").submit(function(event) {
        event.preventDefault();
        if(!onLoading) {
            onLoading = true;
            const _f = this;
            $(`button[type="submit"]`, _f).html(`<i class="fa fa-spinner fa-spin"></i> Loading...`);
           
            var formData = new FormData(this);
            $.ajax({
                url: this.action,
                type: 'POST',
                dataType: 'json',
                processData: false,
                contentType: false,
                data: formData,
            })
            .done(function(response, textStatus, jqXHR) {
                const temp = $(`#tb-row`).clone(true).contents();
                $(`[data-id="index"]`, temp).text( index.toString().concat('.') );
                $(`[data-id="title"]`, temp).text(response.title);
                $(`a[href]`, temp).prop({
                    'href': `/mp3/${response.videoId}`
                }).on('click', function(event){
                    event.preventDefault();
                    const parent = this;
                    $(this).off('click');
                    $(this).html( `<i class="fa fa-spinner fa-spin"></i> Process...` );
                    var xhr = new XMLHttpRequest();
                    xhr.open('GET', `/mp3/${response.videoId}`, true);
                    xhr.responseType = 'blob';
                    xhr.onprogress = e => {
                        const kb = Intl.NumberFormat().format( Math.round(e.loaded / 1000) );
                        $(parent).html(`DL ${kb} KB`)
                    }
                    xhr.onload = e => {
                        console.log(xhr.response);
                        const url = window.URL.createObjectURL(xhr.response);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `${response.title}.mp3`;
                        a.className = 'btn btn-primary btn-sm';
                        a.innerHTML = `<i class="fa fa-download"></i> Download`;
                        $(`[data-id="url"]`, temp).empty().append(a);
                    }
                    xhr.send()
                });
                $(`#table tbody`).append(temp);
                index++;
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                if(jqXHR.responseJSON ?? false) {
                    const json = jqXHR.responseJSON;
                    alert(json.message);
                }
            })
            .always(function() {
                onLoading = false;
                $(`button[type="submit"]`, _f).html(`Submit`);
            });
        } 
    });
});